import xml.etree.ElementTree as xmlET
from tkinter import ttk
import uuid
from math import inf
from .drivers import TKMLDriver
from .exceptions import TKMLInvalidElement, TKMLMalformedElement, TKMLRuntimeError


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

def make_call(master: TKMLDriver, function_name: str) -> callable:
    def _call():
        func = getattr(master, function_name, None)
        if not callable(func):
            raise TKMLRuntimeError(
                f"Attempted to call undefined function [{function_name}].\n"
                "Make sure that function is defined by the master widget."
            )
        func()

    return _call


def virtual_method(master: TKMLDriver, function: str) -> callable:
    function_data = parse_dict(function)

    print("making virtual method", function_data)

    function_name = function_data["name"]

    if function_name == "set_toggle":
        widget = function_data["widget"]
        variable = function_data["variable"]
        onvalue = function_data["onvalue"]
        offvalue = function_data["offvalue"]

        def _call(*args):
            print("calling virtual method: toggle")
            if master._tkml_variables[variable].get() == onvalue:
                master._tkml_variables[widget].enable()
            elif master._tkml_variables[variable].get() == offvalue:
                master._tkml_variables[widget].disable()

        # update the frame on init
        master._on_init.append(_call)
        return _call
    else:
        raise TKMLInvalidElement("Unrecognized Virtual Method", function)


def lookup(master: TKMLDriver, id_: int):
    return master._tkml_variables[id_]

def pull_layout_attributes(node: xmlET.Element):
    """Remove Layout Params from Element Attributes and return them

    Pulls: rowspan, columnspan, side, sticky, fill, expand
    """
    # Removes the layout manager keywords from the node attributes
    layout_params = {}
    if "rowspan" in node.attrib:
        layout_params["rowspan"] = int(node.attrib["rowspan"])
        node.attrib.pop("rowspan")

    if "columnspan" in node.attrib:
        layout_params["columnspan"] = int(node.attrib["columnspan"])
        node.attrib.pop("columnspan")

    if "side" in node.attrib:
        layout_params["side"] = node.attrib["side"]
        node.attrib.pop("side")

    if "sticky" in node.attrib:
        layout_params["sticky"] = node.attrib["sticky"]
        node.attrib.pop("sticky")

    if "fill" in node.attrib:
        layout_params["fill"] = node.attrib["fill"]
        node.attrib.pop("fill")

    if "expand" in node.attrib:
        layout_params["expand"] = node.attrib["expand"]
        node.attrib.pop("expand")

    return layout_params

def get_tooltip(node: xmlET.Element) -> str | None:
    if "tooltip" in node.attrib:
        return node.attrib.pop("tooltip")
    else:
        return None

def patch_attributes(master: TKMLDriver, node: xmlET.Element):
    """Convert the node's attributes to python values inplace"""
    # Autoconvert numbers
    for attribute in node.attrib:
        # Escape numbers if the start with '/'
        if (
            node.attrib[attribute].startswith("/")
            and node.attrib[attribute][1:].isdigit()
        ):
            node.attrib[attribute] = node.attrib[attribute][1:]
            continue
        # Convert digits into numbers
        if node.attrib[attribute].isdigit():
            node.attrib[attribute] = int(node.attrib[attribute])

        elif node.attrib[attribute] == "MATH_INF":
            node.attrib[attribute] = inf
            
        elif node.attrib[attribute] == "-MATH_INF":
            node.attrib[attribute] = -inf

    if "command" in node.attrib:
        if node.attrib["command"].startswith("@"):  # Virtual Method
            node.attrib["command"] = virtual_method(master, node.attrib["command"][1:])
        else:
            node.attrib["command"] = make_call(master, node.attrib["command"])

    if "textvariable" in node.attrib:
        node.attrib["textvariable"] = lookup(master, node.attrib["textvariable"])

    if "variable" in node.attrib:
        node.attrib["variable"] = lookup(master, node.attrib["variable"])

    if "columns" in node.attrib:
        node.attrib["columns"] = parse_list(node.attrib["columns"])

    if "values" in node.attrib:
        node.attrib["values"] = parse_list(node.attrib["values"])

    if "inline_style" in node.attrib:
        inline_style_attribs = parse_dict(node.attrib["inline_style"])
        node.attrib.pop("inline_style")
        style_name = str(uuid.uuid4()) + "." + ("T" + node.tag)
        #dprint("New Inline Style", style_name, inline_style_attribs)
        ttk.Style().configure(style_name, **inline_style_attribs)
        node.attrib["style"] = style_name

    if "image" in node.attrib:
        node.attrib["image"] = lookup(master, node.attrib["image"])


def get_id(node: xmlET.Element) -> str | None:
    """Remove the 'id' attribute from node and return it if it exists"""
    if "id" in node.attrib:
        return node.attrib.pop("id")
    else:
        return None