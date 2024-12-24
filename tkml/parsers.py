def parse_list(text: str) -> list:
    """
    Take a list of comma seperated values and convert it to a list

    values are auto-converted to int if they don't contain letters
    """
    stripped_values = (value.strip(" ") for value in text.split(" "))
    converted_values = [(int(value) if value.isdigit() else value) for value in stripped_values]
    return converted_values


def parse_dict(text: str) -> dict:
    """
    Take a list of comma seperated values and convert it to a dict.
    Ignores extra whitespace
    Text is formatted like this "key = value; key2 = value2;"
    """
    dict_ = {}
    keybuffer = ""
    valuebuffer = ""
    c_buffer = "key"
    for ch in text:
        if ch == ";": #We arrived at the end of the value
            if "," in valuebuffer: #The value is a list
                dict_[keybuffer] = parse_list(valuebuffer)
            else:
                if valuebuffer.isdigit():
                    dict_[keybuffer] = int(valuebuffer)
                else:
                    dict_[keybuffer] = valuebuffer

            keybuffer = ""
            valuebuffer = ""
            ignoring_spaces_until_letter = True
            c_buffer = "key"
            continue

        if ch == "=":
            c_buffer = "value"
            ignoring_spaces_until_letter = True
            continue

        if ch == " " and ignoring_spaces_until_letter:
            continue

        #We've reached a significant character
        ignoring_spaces_until_letter = False
        if c_buffer == "key":
            keybuffer += ch
        elif c_buffer == "value":
            valuebuffer += ch
    #dprint(f"Parse Dict {text} -> {dict_}")
    return dict_