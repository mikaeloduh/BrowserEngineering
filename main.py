import socket
import ssl
import sys
import logging
import tkinter

# Configure logging to display messages on the console
logging.basicConfig(level=logging.INFO)

# Cache to store open sockets keyed by (scheme, host, port)
sockets = {}


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
        self.port = None

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
        global sockets  # Use the global sockets cache
        address = (self.scheme, self.host, self.port)
        s = sockets.get(address)

        try:
            if s is None:
                logging.info(f"Creating new socket to {self.host}:{self.port}")
                s = socket.socket(
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM,
                    proto=socket.IPPROTO_TCP,
                )
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((self.host, self.port))

                # Upgrade to SSL/TLS if needed
                if self.scheme == "https":
                    ctx = ssl.create_default_context()
                    s = ctx.wrap_socket(s, server_hostname=self.host)

                # Save the socket in the cache
                sockets[address] = s
            else:
                logging.info(f"Reusing existing socket to {self.host}:{self.port}")

            # Create headers dictionary for easier management
            headers = {
                "Host": self.host,
                "User-Agent": "toy-browser/1.0",
                "Connection": "keep-alive",  # Explicitly set keep-alive
            }

            # Build request with headers
            request = f"GET {self.path} HTTP/1.1\r\n"
            for header, value in headers.items():
                request += f"{header}: {value}\r\n"
            request += "\r\n"

            # Send the request to the server, encoded as a byte string
            s.send(request.encode("utf-8"))

            # Read the server's response
            response = s.makefile("rb")
            status_line = response.readline().decode("utf-8")
            version, status, explanation = status_line.strip().split(" ", 2)

            # Read the response headers
            response_headers = {}
            while True:
                line = response.readline()
                if line == b"\r\n":
                    break
                header_line = line.decode("utf-8").strip()
                header, value = header_line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            # Ensure no unsupported transfer encodings are used
            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

            # Read the response body based on Content-Length
            content_length = int(response_headers.get("content-length", 0))
            content = response.read(content_length).decode("utf-8")

        except (socket.error, ssl.SSLError) as e:
            # Remove the socket from the cache on error
            if address in sockets:
                del sockets[address]
            s.close()
            raise e
        except Exception as e:
            # On any other exception, ensure the socket is closed
            if address in sockets:
                del sockets[address]
            s.close()
            raise e

        # Do not close the socket here to keep it alive
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


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()

        # Scroll position
        self.scroll = 0

        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<Down>", self.scroll_down)

    def load(self, url):
        body = url.request()
        self.display_list = layout(body)
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        for x, y, c in self.display_list:
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scroll_up(self, event):
        self.scroll -= SCROLL_STEP
        self.draw()

    def scroll_down(self, event):
        self.scroll += SCROLL_STEP
        self.draw()


def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
    
    return display_list


if __name__ == "__main__":
    # Default to opening the test.html file in the same directory
    default_url = "file://test.html"
    url_str = sys.argv[1] if len(sys.argv) > 1 else default_url
    url = URL(url_str)

    Browser().load(url)
    tkinter.mainloop()
