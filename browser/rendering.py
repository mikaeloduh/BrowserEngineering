HSTEP, VSTEP = 13, 18

def layout(text):
    """
    Takes processed text and creates a display list of characters with their positions.
    """
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == '\n':
            # For paragraph breaks, increase cursor_y by more than VSTEP
            cursor_y += VSTEP
            cursor_x = HSTEP
        else:
            if cursor_x >= 800 - HSTEP:  # Using 800 as default WIDTH
                cursor_y += VSTEP
                cursor_x = HSTEP
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP
    return display_list


def render(content):
    """
    Processes HTML content by removing tags and handling basic entities.
    """
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
