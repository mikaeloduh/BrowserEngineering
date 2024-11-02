import socket

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme == "http"

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,  # Use IPv4
            type=socket.SOCK_STREAM,  # Use stream sockets
            proto=socket.IPPROTO_TCP,  # Use TCP protocol for the socket
        )
        s.connect((self.host, 80))

        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\n"
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
    load(sys.argv[1])

if __name__ == "__main__":
    main()
