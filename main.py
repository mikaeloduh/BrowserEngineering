#!/usr/bin/env python3
"""
Simple Browser Engine - Main Program

This program is a simple browser implementation that can be used to browse basic HTML pages.
Current supported features include:
- Reading local HTML files
- Reading HTTP/HTTPS web pages
- Basic HTML tag processing
- Basic scrolling functionality
"""

import sys
import tkinter

# Import required components from modules
from browser.gui import Browser


# Main program entry point
def main():
    # Default to opening local test file
    default_url = "file://test.html"
    url_str = sys.argv[1] if len(sys.argv) > 1 else default_url

    browser = Browser()
    browser.load(url_str)
    tkinter.mainloop()


if __name__ == "__main__":
    main()
