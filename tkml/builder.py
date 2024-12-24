import tkinter as tk
import tkinter.ttk as ttk
from functools import partial
import xml.etree.ElementTree as xmlET
import datetime
import uuid
from math import inf

from .builder import TKMLDriver
from .widgets import ToggleFrame, TKMLTreeView, CreateToolTip
from .parsers import parse_list, parse_dict, patch_attributes, pull_layout_attributes, get_id, get_tooltip
from .exceptions import TKMLInvalidElement, TKMLMalformedElement, TKMLRuntimeError

DEBUG = False

if DEBUG:
    dprint = print
else:
    def dprint(*args, **kwargs):
        return None

"""
I'm aware that this is not the best way to do this, and
it was hacked together as parts were needed.
The TMKLWidget class is now preferred because it allows you
to store the xml and instantiate new widgets in a cleaner way,
but it still uses this big thang
"""
class TKMLWidgetBuilder:
    def __init__(self, print_debug=True, parser=None):
        def make_handle_terminal(widget):
            return lambda master, node, parent: self._handle_terminal(master, node, parent, widget)
        
        def make_handle_branching(widget):
            return lambda master, node, parent: self._handle_branching(master, node, parent, widget)
        
        self.terminals = {
            "Label":       make_handle_terminal(ttk.Label),
            "Button":      make_handle_terminal(ttk.Button),
            "Entry":       make_handle_terminal(ttk.Entry),
            "Text":        make_handle_terminal(tk.Text),
            "Checkbutton": make_handle_terminal(ttk.Checkbutton),
            "Radiobutton": make_handle_terminal(ttk.Radiobutton),
            "Spinbox":     make_handle_terminal(ttk.Spinbox),
            "Combobox":    make_handle_terminal(ttk.Combobox),
            "Scale":       make_handle_terminal(ttk.Scale),
            # Special Items
            "Table":       self._handle_terminal_table,
            "OptionMenu":  self._handle_terminal_optionmenu,
        }
        self.commands = {
            "RowConfigure":    self._handle_command,
            "ColumnConfigure": self._handle_command,
            "Heading":         self._handle_command,
            "Column":          self._handle_command,
            "Bind":            self._handle_command,
            "String":          self._handle_command,
            "Int":             self._handle_command,
            "Style":           self._handle_command,
            "PhotoImage":      self._handle_command,
            "Title":           self._handle_command,
            "GetVar":          self._handle_command,
            "Geometry":        self._handle_command,
        }
        self.branching = {
            "LabelFrame":  make_handle_branching(ttk.LabelFrame),
            "Frame":       make_handle_branching(ttk.Frame),
            "ToggleFrame": make_handle_branching(ToggleFrame),
            "Notebook":    self._handle_notebook,
            "Toplevel": lambda master, node, parent: self._handle_toplevel(
                master, node, parent, ttk.Toplevel
            ),
        }
        self.layouts = {
            "V":    self._layout_V,
            "H":    self._layout_H,
            "Grid": self._layout_Grid,
        }

        self.print_debug = print_debug
        self.parser = parser

    def add_terminal(self, widget_name, widget):
        self.terminals[widget_name] = (
            lambda master, node, parent: self._handle_terminal(
                master, node, parent, widget
            )
        )

    def add_command(self, command_name, command):
        self.commands[command_name] = lambda master, node, parent: command(
            self, master, node, parent
        )

    def add_branching(self, widget_name, widget):
        self.branching[widget_name] = (
            lambda master, node, parent: self._handle_branching(
                master, node, parent, widget
            )
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
            raise TKMLMalformedElement("OptionMenu must have options value")

        if "textvariable" not in node.attrib:
            raise TKMLMalformedElement("OptionMenu must have textvariable")

        options = parse_list(node.attrib["options"])
        node.attrib.pop("options")
        textvariable = node.attrib.pop("textvariable")
        textvariable.set(options[0])
        widget = ttk.OptionMenu(
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
        tooltip = get_tooltip(node)

        widget = widget_type(parent, **node.attrib)

        if id_ is not None:
            master._tkml_variables[id_] = widget

        if node.tag == "Checkbutton":
            # Fix for checkbutton not working right
            widget.state(["!alternate"])

        if tooltip is not None:
            CreateToolTip(widget, tooltip)

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
            print(node.attrib)
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
                    f"Found Terminal or Branching Element [{row.tag}] as direct child of a Grid-Layouted Branching Element"
                )

            column_index = 0
            for child in row:
                layout_attributes = pull_layout_attributes(child)
                if child.tag != "Empty":
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
                    for r in range(rowspan):
                        if (column_index + r, row_index) in occupied:
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
                if child.tag != "Empty":
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

    def _handle_notebook(self, master, node: xmlET.Element, parent: tk.Widget):
        patch_attributes(master, node)
        id_ = get_id(node)

        notebook_widget = ttk.Notebook(parent, **node.attrib)

        for child in node:
            if child.tag in self.commands:
                self._handle_command(master, child, notebook_widget)
                continue
            tabname = child.tag
            if "tabname" in child.attrib:
                tabname = child.attrib.pop("tabname")

            child_widget = self._handle_any(master, child, notebook_widget)

            notebook_widget.add(child_widget, text=tabname)

        if id_ is not None:
            master._tkml_variables[id_] = notebook_widget

        return notebook_widget

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
        if hasattr(master, "_tkml_init"):
            master._tkml_init()
        if hasattr(master, "init"):
            master.init()

    def build_tkml_from_file(self, master: TKMLDriver, filepath: str):
        self.build_tkml(master, xmlET.parse(filepath, self.parser).getroot())

    def build_tkml_from_string(self, master: TKMLDriver, xmlstring: str):
        self.build_tkml(master, xmlET.fromstring(xmlstring, self.parser))

class TKMLWidget():
    def __init__(self, filepath, parser=None):
        self.filepath = filepath
        # Hopefully this makes it a bit more efficient to instantiate
        # by storing the already parsed xml
        self.xml = xmlET.parse(filepath, parser).getroot()
        self.builder = TKMLWidgetBuilder()

    def new(self, master):
        self.builder.build_tkml(master, self.xml)