import tkinter as tk
import tkinter.ttk as ttk
from functools import partial
import xml.etree.ElementTree as xmlET
import datetime
import uuid
from string import ascii_letters

"""
A Single-File Library for Using XML to layout TKinter


Authored by Randy Graham Jr.
"""

DEBUG = False

if DEBUG:
    dprint = print
else:
    dprint = lambda *args, **kwargs: None


def dformat_node(node):
    if node.text is not None:
        text = "".join([c for c in node.text if c in ascii_letters])
        if text != "":
            return (
                node.tag
                + "("
                + text
                + ", "
                + ", ".join([f"{k} = {v}" for k, v in node.attrib.items()])
                + ")"
            )
    return (
        node.tag
        + "("
        + ", ".join([f"{k} = {v}" for k, v in node.attrib.items()])
        + ")"
    )

    


def parse_list(text: str) -> list:
    """Take a list of comma seperated values and convert it to a list

    values are auto-converted to int if they don't contain letters
    """
    return [
        int(stripped_value) if stripped_value.isdigit() else stripped_value
        for stripped_value in [
            value.strip(" ") for value in text.split(",")
        ]
    ]


def parse_dict(text: str) -> dict:
    """Take a list of comma seperated values and convert it to a dict

    Text is formatted like this "key = value; key2 = value2;"
    """
    dict_ = {}
    keybuffer = ""
    valuebuffer = ""
    c_buffer = "key"
    for ch in text:
        if ch == ";":
            if "," in valuebuffer:
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
        ignoring_spaces_until_letter = False
        if c_buffer == "key":
            keybuffer += ch
        elif c_buffer == "value":
            valuebuffer += ch
    dprint(f"Parse Dict {text} -> {dict_}")
    return dict_

"""
This Sortable treeview class was made by Remi Hassan
https://stackoverflow.com/users/6424190/rami-hassan
https://stackoverflow.com/a/63432251
"""
class SortableTreeview(ttk.Treeview):
    def heading(self, column, sort_by=None, **kwargs):
        if sort_by and not hasattr(kwargs, "command"):
            func = getattr(self, f"_sort_by_{sort_by}", None)
            if func:
                kwargs["command"] = partial(func, column, False)
        return super().heading(column, **kwargs)

    def _sort(self, column, reverse, data_type, callback):
        l = [(self.set(k, column), k) for k in self.get_children("")]
        l.sort(key=lambda t: data_type(t[0]), reverse=reverse)
        for index, (_, k) in enumerate(l):
            self.move(k, "", index)
        self.heading(column, command=partial(callback, column, not reverse))

    def _sort_by_num(self, column, reverse):
        self._sort(column, reverse, int, self._sort_by_num)

    def _sort_by_name(self, column, reverse):
        self._sort(column, reverse, str, self._sort_by_name)

    def _sort_by_date(self, column, reverse):
        def _str_to_datetime(string):
            return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

        self._sort(column, reverse, _str_to_datetime, self._sort_by_date)


class TKMLTreeView(ttk.Frame):
    """A ttk Treeview based on Remi Hassan's SortableTreeview with automatic resizing and scrollbars"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent)

        self.treeview = SortableTreeview(self, **kwargs)

        self.v_scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.treeview.yview
        )
        self.h_scrollbar = ttk.Scrollbar(
            self, orient="horizontal", command=self.treeview.xview
        )
        self.treeview.configure(
            yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set
        )

        self.v_scrollbar.pack(side="right", fill="y")

        self.treeview.pack(expand=1, fill="both")

        self.h_scrollbar.pack(fill="x")

    def __getattr__(self, name):
        # Pass all calls to the treeview
        if name == "treeview":
            # If this is not here it will recur infinitely
            raise AttributeError()
        if hasattr(self.treeview, name):
            return getattr(self.treeview, name)


class TKMLWidget(ttk.Frame):
    """Master Widget for TKML based on ttk Frame

    Contains special variables which the xml transformer depends on
    """

    def __init__(self, parent):
        super().__init__(parent)
        self._tkml_variables = {}
        self._widget_tree = None

    def __getitem__(self, key):
        return self._tkml_variables[key]


class TKMLTopLevel(tk.Toplevel):
    """Master Widget for TKML based on ttk Toplevel

    Contains special variables which the xml transformer depends on
    """

    def __init__(self):
        super().__init__()
        self._tkml_variables = {}
        self._widget_tree = None

    def __getitem__(self, key):
        return self._tkml_variables[key]

    def close(self):
        if "_tkml_on_close" in self._tkml_variables:
            self["_tkml_on_close"]()
        self.destroy()
        self.update()


branching = {"LabelFrame": ttk.LabelFrame, "Frame": ttk.Frame, "Toplevel": tk.Toplevel}
terminal = {
    "Label": ttk.Label,
    "Button": ttk.Button,
    "Entry": ttk.Entry,
    "Table": TKMLTreeView,
    "OptionMenu": ttk.OptionMenu,
    "Text": tk.Text
}
commands = {
    "RowConfigure",
    "ColumnConfigure",
    "Heading",
    "Column",
    "Bind",
    "String",
    "Int",
    "Style",
    "PhotoImage",
    "Title",
    "GetVar",
    "Geometry"
}
item_classes = {
    "Button": "TButton",
    "Label": "TLabel",
    "Entry": "TEntry",
    "Frame": "TFrame",
    "LabelFrame": "TLabelFrame",
}

class TKMLRuntimeError(Exception): pass

def _make_call(master: TKMLWidget, function_name: str) -> callable:
    def _call():
        func = getattr(master, function_name)
        if not callable(func):
            raise TKMLRuntimeError(f"Attempted to call undefined function [{function_name}]. Make sure that function is defined by the master widget.")
        func()
    return lambda: _call()


def _lookup(master: TKMLWidget, id_: int):
    return master._tkml_variables[id_]


def _pull_layout_params(node: xmlET.Element):
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


def _patch_attributes(master: TKMLWidget, node: xmlET.Element):
    """Convert the node's attributes inplace"""
    # Autoconvert numbers
    for attribute in node.attrib:
        # Escape numbers
        if (
            node.attrib[attribute].startswith("/")
            and node.attrib[attribute][1:].isdigit()
        ):
            node.attrib[attribute] = node.attrib[attribute][1:]
            continue
        if node.attrib[attribute].isdigit():
            node.attrib[attribute] = int(node.attrib[attribute])

    if "command" in node.attrib:
        node.attrib["command"] = _make_call(master, node.attrib["command"])

    if "textvariable" in node.attrib:
        node.attrib["textvariable"] = _lookup(master, node.attrib["textvariable"])

    if "columns" in node.attrib:
        node.attrib["columns"] = parse_list(node.attrib["columns"])

    if "inline_style" in node.attrib:
        inline_style_attribs = parse_dict(node.attrib["inline_style"])
        node.attrib.pop("inline_style")
        style_name = str(uuid.uuid4()) + "." + item_classes[node.tag]
        dprint("New Inline Style", style_name, inline_style_attribs)
        ttk.Style().configure(style_name, **inline_style_attribs)
        node.attrib["style"] = style_name

    if "image" in node.attrib:
        node.attrib["image"] = _lookup(master, node.attrib["image"])


def handle_terminal(
    master: TKMLWidget, node: xmlET.Element, parent: tk.Widget
) -> tk.Widget:
    if node.tag not in terminal:
        raise Exception(f"Expected Terminal Node got {node.tag}")

    dprint("TERMINAL", dformat_node(node))
    _patch_attributes(master, node)
    # Patch ID Attribute
    id_ = None
    if "id" in node.attrib:
        id_ = node.attrib["id"]
        node.attrib.pop("id")

    # Widget Specific handlers
    if node.tag == "OptionMenu":
        if "options" not in node.attrib:
            raise Exception(f"OptionMenu must have options value")

        if "textvariable" not in node.attrib:
            raise Exception(f"OptionMenu must have textvariable")

        options = parse_list(node.attrib["options"])
        node.attrib.pop("options")
        textvariable = node.attrib.pop("textvariable")
        textvariable.set(options[0])
        widget = terminal[node.tag](
            parent, textvariable, options[0], *options, **node.attrib
        )

    else:
        widget = terminal[node.tag](parent, **node.attrib)

    if node.tag == "Table":  # Table can have commands as children
        for child in node:
            handle_command(master, child, widget)

    # Add ID Attribute to Master
    if id_ is not None:
        master._tkml_variables[id_] = widget

    return widget


def handle_branching(
    master: TKMLWidget, node: xmlET.Element, parent: tk.Widget
) -> tk.Widget:
    if node.tag not in branching:
        raise Exception(f"Expected Branching Node got {node.tag}")

    dprint("BRANCHING", dformat_node(node))
    _patch_attributes(master, node)

    if "layout" in node.attrib:
        layout_type = node.attrib["layout"]
        node.attrib.pop("layout")
    else:
        # Default to Vertical Layout
        layout_type = "V"

    # Patch ID Attribute
    id_ = None
    if "id" in node.attrib:
        id_ = node.attrib["id"]
        node.attrib.pop("id")
    
    rowweight = columnweight = None
    if "rowweight" in node.attrib:
        rowweight = node.attrib.pop("rowweight")
    if "columnweight" in node.attrib:
        columnweight = node.attrib.pop("columnweight")

    widget = branching[node.tag](parent, **node.attrib)

    # Add ID Attribute to Master
    if id_ is not None:
        master._tkml_variables[id_] = widget

    if layout_type == "Grid":
        dprint("LAYOUT TYPE: Grid")
        row_max = 0
        column_max = 0
        occupied = {}
        row_index = 0
        for row in node:
            if row.tag != "Row":
                # Must be command or Row
                child = handle_command(master, row, widget)
                continue
            assert row.tag == "Row"
            column_index = 0
            for child in row:
                # Pass over cells until an unoccupied one is found
                while (column_index, row_index) in occupied:
                    column_index += 1

                layout_attributes = _pull_layout_params(child)
                dprint(f"ROW: {row_index}, COLUMN: {column_index}")
                child_widget = handle_any(master, child, widget)

                if (
                    child_widget is None or child.tag == "Toplevel"
                ):
                    #We must skip things which can't be packed.
                    #This also prevents the widget from
                    #being added to the occupied list
                    continue

                child_widget.grid(
                    row=row_index, column=column_index, **layout_attributes
                )
                column_max = max(column_max, column_index)
                row_max = max(row_max, row_index)

                # Set all grid cells as occupied
                rowspan = (
                    layout_attributes["rowspan"]
                    if "rowspan" in layout_attributes
                    else 1
                )
                columnspan = (
                    layout_attributes["columnspan"]
                    if "columnspan" in layout_attributes
                    else 1
                )
                dprint("rowspan", rowspan, "columnspan", columnspan)

                for x in range(column_index, column_index + columnspan):
                    for y in range(row_index, row_index + rowspan):
                        occupied[(x, y)] = True

            row_index += 1

        if rowweight is not None:
            for r in range(0, row_max+1):
                widget.grid_rowconfigure(r, weight=rowweight)
        if columnweight is not None:
            for c in range(0, column_max+1):
                widget.grid_columnconfigure(c, weight=columnweight)
        return widget
    
    if layout_type == "H":
        # Horizontal
        for index, child in enumerate(node):
            layout_attributes = {"expand": 1, "fill": "both"}

            child_widget = handle_any(master, child, widget)
            layout_attributes.update(_pull_layout_params(child))
            if child_widget is None or child.tag == "Toplevel":
                continue
            child_widget.pack(side="left", **layout_attributes)
        return widget
    
    if layout_type == "V":
        # Vertical
        for index, child in enumerate(node):
            layout_attributes = {"expand": 1, "fill": "both"}

            child_widget = handle_any(master, child, widget)
            layout_attributes.update(_pull_layout_params(child))
            
            if child_widget is None or child.tag == "Toplevel":
                continue
            child_widget.pack(**layout_attributes)
        return widget


def handle_command(master: TKMLWidget, node: xmlET.Element, parent: tk.Widget) -> None:
    if node.tag not in commands:
        raise Exception(f"Expected Command Node got {node.tag}")

    _patch_attributes(master, node)

    dprint("command", node.tag, node.attrib)
    if node.tag == "RowConfigure":
        parent.grid_rowconfigure(int(node.text), **node.attrib)

    elif node.tag == "ColumnConfigure":
        parent.grid_columnconfigure(int(node.text), **node.attrib)

    elif node.tag == "Geometry":
        parent.winfo_toplevel().geometry(node.text)

    elif node.tag == "Heading":
        parent.heading(node.text, **node.attrib)

    elif node.tag == "Column":
        parent.column(node.text, **node.attrib)

    elif node.tag == "Bind":
        master.bind(node.text, **node.attrib)

    elif node.tag == "String":
        id_ = node.attrib.pop("id")
        master._tkml_variables[id_] = tk.StringVar(**node.attrib)

    elif node.tag == "Int":
        id_ = node.attrib.pop("id")
        master._tkml_variables[id_] = tk.IntVar(**node.attrib)

    elif node.tag == "Style":
        ttk.Style().configure(node.text, **node.attrib)

    elif node.tag == "PhotoImage":
        id_ = node.attrib["id"]
        node.attrib.pop("id")
        master._tkml_variables[id_] = tk.PhotoImage(**node.attrib)

    elif node.tag == "Title":
        master.winfo_toplevel().title(node.text)

    elif node.tag == "GetVar":
        python_name = node.attrib["python"]
        id_ = node.attrib["id"]
        master._tkml_variables[id_] = getattr(master, python_name)

    return None


def handle_any(
    master: TKMLWidget, node: xmlET.Element, parent: tk.Widget
) -> None | tk.Widget:
    if node.tag in branching:
        return handle_branching(master, node, parent)
    elif node.tag in commands:
        return handle_command(master, node, parent)
    elif node.tag in terminal:
        return handle_terminal(master, node, parent)
    raise Exception(f"Unrecognized Element {node.tag} {node.attrib}")


def build_tkml(master: TKMLWidget, xml_root: xmlET.Element) -> None:
    if type(xml_root) != xmlET.Element:
        raise Exception(
            f"Expected Element Type got {type(xml_root)} Type. Did you forget to call getroot()?"
        )
    layout_attributes = {"expand": 1, "fill": "both"}
    layout_attributes.update(_pull_layout_params(xml_root))
    root_widget = handle_any(master, xml_root, master)
    if root_widget is None or xml_root.tag == "Toplevel":
        return
    root_widget.pack(**layout_attributes)


def build_tkml_from_file(master: TKMLWidget, filepath: str):
    build_tkml(master, xmlET.parse(filepath).getroot())


def build_tkml_from_string(master: TKMLWidget, xmlstring: str):
    build_tkml(master, xmlET.fromstring(xmlstring).getroot())

"""
Dynamically add the builders to the TKML Master widgets

These won't appear in type-checkers unfortunately, but
they are there
"""
__tkml_masters = [TKMLTopLevel, TKMLWidget]
__builders = [build_tkml, build_tkml_from_file, build_tkml_from_string]
for master in __tkml_masters:
    for builder in __builders:
        setattr(master, builder.__name__, builder)
