import tkinter as tk
ttk = tk.ttk

class TKMLDriver(ttk.Frame):
    """Master Widget for TKML based on ttk Frame

    Contains special variables which the xml transformer depends on
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self._tkml_variables = kwargs
        self._widget_tree = None
        self.on_init = []

    def _tkml_init(self):
        for i in self.on_init:
            i()
        self.on_init.clear()

    def __getitem__(self, key):
        return self._tkml_variables[key]


class TKMLTopLevelDriver(tk.Toplevel):
    """Master Widget for TKML based on ttk Toplevel

    Contains special variables which the xml transformer depends on
    """

    def __init__(self, **kwargs):
        super().__init__()
        self._tkml_variables = kwargs
        self._widget_tree = None
        self._on_init = []

    def __getitem__(self, key):
        return self._tkml_variables[key]

    def _tkml_init(self):
        for i in self._on_init:
            i()

    def close(self):
        if "_tkml_on_close" in self._tkml_variables:
            self["_tkml_on_close"]()
        self.destroy()
        self.update()