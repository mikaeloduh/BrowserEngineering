import socket
import ssl
import sys

class URL:
    def __init__(self, url):
        # Handle view-source scheme
        self.view_source = url.startswith("view-source:")
        if self.view_source:
            url = url[len("view-source:"):]  # Remove "view-source:" prefix

        # Handle data URLs which use single colon instead of ://
        if url.startswith("data:"):
            self._parse_data_url(url)
        elif url.startswith("file://"):
            self._parse_file_url(url)
        elif url.startswith(("http://", "https://")):
            self._parse_http_url(url)
        else:
            raise ValueError(f"Unsupported URL scheme in {url}")

    def _parse_data_url(self, url):
        self.scheme = "data"
        self.data = url[len("data:"):]  # Everything after "data:"
        self.host = ""
        self.path = ""

    def _parse_file_url(self, url):
        self.scheme = "file"
        self.host = ""
        self.path = url[len("file://"):]
        self.port = None

    def _parse_http_url(self, url):
        self.scheme, rest = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]  # Supported schemes
        # Handle default ports
        if self.scheme == "http":
            self.port = 80
        else:
            self.port = 443

        # Handle paths
        if "/" not in rest:
            rest += "/"
        self.host, self.path = rest.split("/", 1)
        self.path = "/" + self.path

        # Handle port numbers
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        # Get the content first
        if self.scheme == "file":
            content = self._handle_file_request()
        elif self.scheme == "data":
            content = self.data
        else:
            content = self._handle_network_request()

        # If view-source is enabled, return the raw content
        # Otherwise, return for normal rendering
        return content if self.view_source else self.render(content)

    def _handle_file_request(self):
        try:
            with open(self.path, "r") as f:
                content = f.read()
        except FileNotFoundError:
            content = f"Error: File not found: {self.path}"
        except PermissionError:
            content = f"Error: Permission denied: {self.path}"
        return content

    def _handle_network_request(self):
        s = socket.socket(
            family=socket.AF_INET,  # Use IPv4
            type=socket.SOCK_STREAM,  # Use stream sockets
            proto=socket.IPPROTO_TCP,  # Use TCP protocol for the socket
        )
        address = (self.host, self.port)

        try:
            # First establish TCP connection
            s.connect(address)

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
            status_line = response.readline()
            version, status, explanation = status_line.strip().split(" ", 2)

            # Read the response headers
            response_headers = {}
            while True:
                line = response.readline()
                # If the line is empty, we've reached the end of the headers
                if line == "\r\n":
                    break
                header, value = line.strip().split(":", 1)
                response_headers[header.casefold()] = value.strip()

                assert "transfer-encoding" not in response_headers
                assert "content-encoding" not in response_headers

            # Read the response body
            content = response.read()
        finally:
            s.close()
        return content

    def render(self, content):
        # Move HTML parsing logic here
        result = []
        in_tag = False
        entity = ""
        in_entity = False

        for c in content:
            if in_entity:
                if c == ";":
                    if entity == "lt":
                        result.append("<")
                    elif entity == "gt":
                        result.append(">")
                    else:
                        result.append(f"&{entity};")
                    in_entity = False
                    entity = ""
                else:
                    entity += c
            elif c == "&":
                in_entity = True
                entity = ""
            elif c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                result.append(c)
        return ''.join(result)

def show(body):
    print(body, end="")

def load(url):
    body = url.request()
    show(body)

def main():
    # Default to opening the test.html file in the same directory
    default_url = "file://test.html"
    url_str = sys.argv[1] if len(sys.argv) > 1 else default_url
    load(URL(url_str))

if __name__ == "__main__":
    main()
