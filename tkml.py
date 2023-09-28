"""
A Single-File Library for Using XML to layout TKinter
"""

__version__ = "1.0.0"
__author__ = "Randy Graham"

import tkinter as tk
import tkinter.ttk as ttk
from functools import partial
import xml.etree.ElementTree as xmlET
import datetime
import uuid
from string import ascii_letters

DEBUG = False

if DEBUG:
    dprint = print
else:
    dprint = lambda *args, **kwargs: None


class TKMLInvalidElement(Exception):
    pass


class TKMLRuntimeError(Exception):
    pass


class TKMLMalformedElement(Exception):
    pass


def parse_list(text: str) -> list:
    """Take a list of comma seperated values and convert it to a list

    values are auto-converted to int if they don't contain letters
    """
    return [
        int(stripped_value) if stripped_value.isdigit() else stripped_value
        for stripped_value in [value.strip(" ") for value in text.split(",")]
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


def make_call(master: TKMLWidget, function_name: str) -> callable:
    def _call():
        func = getattr(master, function_name)
        if not callable(func):
            raise TKMLRuntimeError(
                f"Attempted to call undefined function [{function_name}]. Make sure that function is defined by the master widget."
            )
        func()

    return _call


def lookup(master: TKMLWidget, id_: int):
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


def patch_attributes(master: TKMLWidget, node: xmlET.Element):
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
        node.attrib["command"] = make_call(master, node.attrib["command"])

    if "textvariable" in node.attrib:
        node.attrib["textvariable"] = lookup(master, node.attrib["textvariable"])

    if "columns" in node.attrib:
        node.attrib["columns"] = parse_list(node.attrib["columns"])

    if "inline_style" in node.attrib:
        inline_style_attribs = parse_dict(node.attrib["inline_style"])
        node.attrib.pop("inline_style")
        style_name = str(uuid.uuid4()) + "." + ("T" + node.tag)
        dprint("New Inline Style", style_name, inline_style_attribs)
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


class TKMLWidgetBuilder:
    def __init__(self, print_debug=True, parser=None):
        self.terminals = {
            "Label": lambda master, node, parent: self._handle_terminal(
                master, node, parent, ttk.Label
            ),
            "Button": lambda master, node, parent: self._handle_terminal(
                master, node, parent, ttk.Button
            ),
            "Entry": lambda master, node, parent: self._handle_terminal(
                master, node, parent, ttk.Entry
            ),
            "Text": lambda master, node, parent: self._handle_terminal(
                master, node, parent, tk.Text
            ),
            "Checkbutton": lambda master, node, parent: self._handle_terminal(
                master, node, parent, ttk.Checkbutton
            ),
            # Special Items
            "Table": self._handle_terminal_table,
            "OptionMenu": self._handle_terminal_optionmenu,
        }
        self.commands = {
            "RowConfigure": self._handle_command,
            "ColumnConfigure": self._handle_command,
            "Heading": self._handle_command,
            "Column": self._handle_command,
            "Bind": self._handle_command,
            "String": self._handle_command,
            "Int": self._handle_command,
            "Style": self._handle_command,
            "PhotoImage": self._handle_command,
            "Title": self._handle_command,
            "GetVar": self._handle_command,
            "Geometry": self._handle_command,
        }
        self.branching = {
            "LabelFrame": lambda master, node, parent: self._handle_branching(
                master, node, parent, ttk.LabelFrame
            ),
            "Frame": lambda master, node, parent: self._handle_branching(
                master, node, parent, ttk.Frame
            ),
            "Toplevel": lambda master, node, parent: self._handle_toplevel(
                master, node, parent, ttk.Toplevel
            ),
        }
        self.layouts = {
            "V": self._layout_V,
            "H": self._layout_H,
            "Grid": self._layout_Grid,
        }

        self.print_debug = print_debug
        self.parser = parser

    def add_terminal(self, widget_name, widget):
        self.terminals[
            widget_name
        ] = lambda master, node, parent: self._handle_terminal(
            master, node, parent, widget
        )

    def add_command(self, command_name, command):
        self.commands[command_name] = lambda master, node, parent: command(
            self, master, node, parent
        )

    def add_branching(self, widget_name, widget):
        self.branching[
            widget_name
        ] = lambda master, node, parent: self._handle_branching(
            master, node, parent, widget
        )

    def add_layout(self, layout_type, function):
        self.layouts[layout_type] = lambda master, node, parent: function(
            self, master, node, parent
        )

    def _handle_terminal_table(
        self, master, node: xmlET.Element, parent: tk.Widget
    ) -> TKMLTreeView:
        patch_attributes(master, node)

        id_ = get_id(node)

        widget = TKMLTreeView(parent, **node.attrib)

        for child in node:
            if child.tag not in self.commands:
                raise TKMLInvalidElement(
                    f"Cannot have non-command as child of table: {child.tag}"
                )
            self.commands[child.tag](master, child, widget)

        if id_ is not None:
            master._tkml_variables[id_] = widget

        return widget

    def _handle_terminal_optionmenu(
        self, master, node: xmlET.Element, parent: tk.Widget
    ) -> ttk.OptionMenu:
        patch_attributes(master, node)

        id_ = get_id(node)

        if "options" not in node.attrib:
            raise TKMLMalformedElement(f"OptionMenu must have options value")

        if "textvariable" not in node.attrib:
            raise TKMLMalformedElement(f"OptionMenu must have textvariable")

        options = parse_list(node.attrib["options"])
        node.attrib.pop("options")
        textvariable = node.attrib.pop("textvariable")
        textvariable.set(options[0])
        widget = ttk.OptionMenu[node.tag](
            parent, textvariable, options[0], *options, **node.attrib
        )
        if id_ is not None:
            master._tkml_variables[id_] = widget

        return widget

    def _handle_terminal(
        self, master, node: xmlET.Element, parent: tk.Widget, widget_type: tk.Widget
    ) -> tk.Widget:
        if node.tag not in self.terminals:
            raise TKMLInvalidElement(f"Expected Terminal Node got {node.tag}")

        patch_attributes(master, node)

        id_ = get_id(node)

        widget = widget_type(parent, **node.attrib)

        if id_ is not None:
            master._tkml_variables[id_] = widget

        return widget

    def _handle_command(self, master, node: xmlET.Element, parent: tk.Widget) -> None:
        if node.tag not in self.commands:
            raise Exception(f"Expected Command Node got {node.tag}")

        patch_attributes(master, node)

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
            parent.bind(node.text, **node.attrib)

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
            parent.winfo_toplevel().title(node.text)

        elif node.tag == "GetVar":
            python_name = node.attrib["python"]
            id_ = node.attrib["id"]
            master._tkml_variables[id_] = getattr(master, python_name)

        return None

    def _layout_Grid(self, master, node, parent):
        dprint("LAYOUT TYPE: Grid")
        rowweight = node.attrib.pop("rowweight")
        columnweight = node.attrib.pop("columnweight")
        row_max = 0
        column_max = 0
        occupied = {}
        row_index = 0
        for row in node:
            if row.tag in self.commands:
                child = self._handle_command(master, row, parent)
                continue
            elif row.tag != "Row":
                raise TKMLInvalidElement(
                    "Found Terminal or Branching Element [{row.tag}] as direct child of a Grid-Layouted Branching Element"
                )

            column_index = 0
            for child in row:
                layout_attributes = pull_layout_attributes(child)
                child_widget = self._handle_any(master, child, parent)

                if child_widget is None or child.tag == "Toplevel":
                    # We must skip things which can't be packed.
                    # This also prevents the widget from
                    # being added to the occupied list
                    continue

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

                sufficient_space = False
                while not sufficient_space:
                    for r in range(0, rowspan):
                        if (column_index, row_index) in occupied:
                            column_index += 1
                            break
                    else:
                        # There is enough room
                        sufficient_space = True

                # Mark all cells as occupied
                for x in range(column_index, column_index + columnspan):
                    for y in range(row_index, row_index + rowspan):
                        occupied[(x, y)] = True

                # pack the child_widget
                child_widget.grid(
                    row=row_index, column=column_index, **layout_attributes
                )
                column_max = max(column_max, column_index)
                row_max = max(row_max, row_index)

            row_index += 1

        if rowweight is not None:
            for r in range(0, row_max + 1):
                parent.grid_rowconfigure(r, weight=rowweight)
        if columnweight is not None:
            for c in range(0, column_max + 1):
                parent.grid_columnconfigure(c, weight=columnweight)
        return parent

    def _layout_H(self, master, node: xmlET.Element, parent: tk.Widget) -> tk.Widget:
        for index, child in enumerate(node):
            layout_attributes = {"expand": 1, "fill": "both"}

            child_widget = self._handle_any(master, child, parent)
            layout_attributes.update(pull_layout_attributes(child))
            if child_widget is None or child.tag == "Toplevel":
                continue
            child_widget.pack(side="left", **layout_attributes)
        return parent

    def _layout_V(self, master, node: xmlET.Element, parent: tk.Widget) -> tk.Widget:
        for index, child in enumerate(node):
            layout_attributes = {"expand": 1, "fill": "both"}
            child_widget = self._handle_any(master, child, parent)
            layout_attributes.update(pull_layout_attributes(child))
            if child_widget is None or child.tag == "Toplevel":
                continue
            child_widget.pack(**layout_attributes)
        return parent

    def _handle_branching(
        self, master, node: xmlET.Element, parent: tk.Widget, widget_type: tk.Widget
    ) -> tk.Widget:
        patch_attributes(master, node)

        if "layout" in node.attrib:
            layout_type = node.attrib["layout"]
            node.attrib.pop("layout")
        else:
            layout_type = "V"

        # Patch ID Attribute
        id_ = get_id(node)

        rowweight = columnweight = None
        if "rowweight" in node.attrib:
            rowweight = node.attrib.pop("rowweight")
        if "columnweight" in node.attrib:
            columnweight = node.attrib.pop("columnweight")

        widget = widget_type(parent, **node.attrib)

        # The widget itself doesn't accept these, but we need them in the Grid layout
        node.attrib["rowweight"] = rowweight
        node.attrib["columnweight"] = columnweight

        # Add ID Attribute to Master
        if id_ is not None:
            master._tkml_variables[id_] = widget

        return self.layouts[layout_type](master, node, widget)

    def _handle_any(
        self, master, node: xmlET.Element, parent: tk.Widget
    ) -> None | tk.Widget:
        if node.tag in self.terminals:
            return self.terminals[node.tag](master, node, parent)
        elif node.tag in self.commands:
            self.commands[node.tag](master, node, parent)
        elif node.tag in self.branching:
            return self.branching[node.tag](master, node, parent)
        else:
            raise TKMLInvalidElement(f"Recieved unimplemented element {node.tag}")

    def build_tkml(self, master, xml_root):
        if type(xml_root) != xmlET.Element:
            raise TKMLInvalidElement(
                f"Expected Element Type got {type(xml_root)} Type. Did you forget to call getroot()?"
            )
        layout_attributes = {"expand": 1, "fill": "both"}
        layout_attributes.update(pull_layout_attributes(xml_root))
        root_widget = self._handle_any(master, xml_root, master)
        if root_widget is None or xml_root.tag == "Toplevel":
            return
        root_widget.pack(**layout_attributes)

    def build_tkml_from_file(self, master: TKMLWidget, filepath: str):
        self.build_tkml(master, xmlET.parse(filepath, self.parser).getroot())

    def build_tkml_from_string(self, master: TKMLWidget, xmlstring: str):
        self.build_tkml(master, xmlET.fromstring(xmlstring, self.parser).getroot())
