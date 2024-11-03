import socket
import ssl

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]

        if self.scheme == "file":
            self.host = ""
            self.path = url
            return

        if self.scheme == "http":
            self.port = 80
        else:
            self.port = 443

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url
        
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        if self.scheme == "file":
            try:
                with open(self.path, "r") as f:
                    return f.read()
            except FileNotFoundError:
                return f"Error: File not found: {self.path}"
            except PermissionError:
                return f"Error: Permission denied: {self.path}"

        s = socket.socket(
            family=socket.AF_INET,  # Use IPv4
            type=socket.SOCK_STREAM,  # Use stream sockets
            proto=socket.IPPROTO_TCP,  # Use TCP protocol for the socket
        )
        # First establish TCP connection
        s.connect((self.host, self.port))
        
        # Then upgrade to SSL/TLS if needed
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        # This order is important because the SSL/TLS handshake needs to 
        # happen over an already established TCP connection. The SSL/TLS 
        # protocol is built on top of TCP.

        # Create headers dictionary for easier management
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "toy-browser/1.0",
        }

        # Build request with headers
        request = f"GET {self.path} HTTP/1.1\r\n"  # Updated to HTTP/1.1
        for header, value in headers.items():
            request += f"{header}: {value}\r\n"
        request += "\r\n"

        # Send the request to the server, encoded as a byte string
        s.send(request.encode("utf-8"))

        # To read the server’s response, you could use the read function on sockets, 
        # which gives whatever bits of the response have already arrived. Then you 
        # write a loop to collect those bits as they arrive. However, in Python you
        # can use the makefile helper function, which hides the loop
        response = s.makefile("r", encoding="utf-8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        # Read the response headers
        response_headers = {}
        while True:
            line = response.readline()
            # If the line is empty, we've reached the end of the headers
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

        # Read the response body
        content = response.read()
        s.close()

        return content

        
def show(body):
    # Print the body without HTML tags
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

def load(url):
    body = URL(url).request()
    show(body)


def main():
    import sys
    # Default to opening the test.html file in the same directory
    default_url = "file://test.html"
    url = sys.argv[1] if len(sys.argv) > 1 else default_url
    load(url)

if __name__ == "__main__":
    main()
