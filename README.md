# Simple Browser Engine

This project is a simple browser engine implementation for learning and understanding the basic working principles of browsers.

## Features

- Support for reading local HTML files
- Support for reading HTTP/HTTPS pages
- Basic HTML parsing functionality
- Support for basic scrolling operations
- Modular design for easy extension

## Directory Structure

```
browser/
  ├── __init__.py       # Package initialization file
  ├── config.py         # Configuration parameters
  ├── gui.py            # Graphical interface related code
  ├── html_parser.py    # HTML parsing module
  ├── css_parser.py     # CSS parsing module
  ├── networking.py     # Network request handling
  └── rendering.py      # Rendering engine
main.py                 # Program main entry
test.html               # Test HTML file
test-zh.html            # Chinese test HTML file
```

## How to Run

You can run the browser in the following ways:

```bash
# Using the default test page
python main.py

# Specify local HTML file
python main.py file://path/to/your/file.html

# Specify network URL
python main.py https://example.com

# View HTML source code
python main.py view-source:file://test.html
```

## Features and Usage

- Up/Down arrow keys: Scroll page
- URL prefix `view-source:` can view webpage source code

## Future Plans

- Implement complete HTML parser
- Add CSS support
- Add JavaScript engine
- Optimize rendering performance
- Enhance user interface
