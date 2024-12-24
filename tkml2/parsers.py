from tkinter import ttk
import uuid
from math import inf
import xml.etree.ElementTree as xmlET

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
    return dict_

def convert_attributes(node: xmlET.Element):
    """Convert the node's attributes to python values"""
    # Autoconvert numbers
    converted_attributes = {}
    for attribute in node.attrib:
        # Escape numbers if the start with '/'
        if (
            node.attrib[attribute].startswith("/")
            and node.attrib[attribute][1:].isdigit()
        ):
            converted_attributes[attribute] = node.attrib[attribute][1:]
            continue
        # Convert digits into numbers
        if node.attrib[attribute].isdigit():
            converted_attributes[attribute] = int(node.attrib[attribute])

        elif node.attrib[attribute] == "MATH_INF":
            converted_attributes[attribute] = inf
            
        elif node.attrib[attribute] == "-MATH_INF":
            converted_attributes[attribute] = -inf

    if "command" in node.attrib:
        converted_attributes["command"] = node.attrib["command"]
        # if node.attrib["command"].startswith("@"):  # Virtual Method
        #     node.attrib["command"] = node.attrib["command"][1:]
        # else:
        #     node.attrib["command"] = node.attrib["command"]

    if "textvariable" in node.attrib:
        converted_attributes["textvariable"] = node.attrib["textvariable"]
        #node.attrib["textvariable"] = lookup(master, node.attrib["textvariable"])

    if "variable" in node.attrib:
        converted_attributes["variable"] = node.attrib["variable"]
        #node.attrib["variable"] = lookup(master, node.attrib["variable"])

    if "columns" in node.attrib:
        converted_attributes["columns"] = parse_list(node.attrib["columns"])
        #node.attrib["columns"] = parse_list(node.attrib["columns"])

    if "values" in node.attrib:
        converted_attributes["values"] = parse_list(node.attrib["values"])
        #node.attrib["values"] = parse_list(node.attrib["values"])

    if "inline_style" in node.attrib:
        inline_style_attribs = parse_dict(node.attrib["inline_style"])
        #node.attrib.pop("inline_style")
        style_name = str(uuid.uuid4()) + "." + ("T" + node.tag)
        #dprint("New Inline Style", style_name, inline_style_attribs)
        ttk.Style().configure(style_name, **inline_style_attribs)
        converted_attributes["style"] = style_name

    if "image" in node.attrib:
        converted_attributes["image"] = node.attrib["image"]