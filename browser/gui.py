import tkinter

from browser.networking import URL
from browser.rendering import layout, render, HSTEP, VSTEP


WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100


class Browser:
    def __init__(self):
        """Initialize the browser window and UI components."""
        self.window = tkinter.Tk()
        self.window.title("Simple Browser")
        
        # Create URL entry and navigation controls
        self.navigation_frame = tkinter.Frame(self.window)
        self.navigation_frame.pack(fill=tkinter.X, padx=5, pady=5)
        
        self.url_entry = tkinter.Entry(self.navigation_frame)
        self.url_entry.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
        
        self.load_button = tkinter.Button(self.navigation_frame, text="Load", command=self._load_from_entry)
        self.load_button.pack(side=tkinter.RIGHT, padx=5)
        
        # Main canvas for rendering
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT,
            bg="white"
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)

        # Scroll position
        self.scroll = 0
        self.display_list = []

        # Key bindings
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Return>", lambda e: self._load_from_entry())
        
    def _load_from_entry(self):
        """Load URL from entry field."""
        url_str = self.url_entry.get()
        if url_str:
            self.load(url_str)

    def load(self, url_str):
        """Load and display content from the given URL."""
        # Update URL entry
        self.url_entry.delete(0, tkinter.END)
        self.url_entry.insert(0, url_str)
        
        # Reset scroll position
        self.scroll = 0
        
        # Check for 'view-source:' prefix
        view_source = url_str.startswith("view-source:")
        if view_source:
            url_str = url_str[len("view-source:"):]  # Remove 'view-source:' prefix

        url = URL(url_str)
        content = url.request()

        # If view-source is enabled, draw the raw content
        # Otherwise, draw for normal rendering
        if view_source:
            # Display the raw content without rendering
            self.display_list = layout(content)
        else:
            # Render the content before displaying
            rendered_content = render(content)
            self.display_list = layout(rendered_content)

        self.draw()

    def draw(self):
        """Draw the display list on the canvas."""
        self.canvas.delete("all")

        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                # skips characters below the viewing window
                continue
            if y + VSTEP < self.scroll:
                # skips characters above the viewing window
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scroll_up(self, event):
        """Scroll the view up."""
        self.scroll = max(0, self.scroll - SCROLL_STEP)
        self.draw()

    def scroll_down(self, event):
        """Scroll the view down."""
        # Find the maximum y-coordinate in the display_list
        if not self.display_list:
            return
            
        max_y = max(y for x, y, c in self.display_list)
        # Add a step to account for character height
        content_height = max_y + VSTEP
        max_scroll = max(0, content_height - HEIGHT)
        self.scroll = min(self.scroll + SCROLL_STEP, max_scroll)
        self.draw()
