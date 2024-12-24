import tkinter as tk
from functools import partial
import datetime
ttk = tk.ttk

"""
Based on work by Mario Camilleri
https://stackoverflow.com/a/52152773
"""
class ToggleFrame(ttk.Frame):
    def enable(self, state="!disabled"):
        def cstate(widget):
            # Is this widget a container?
            if widget.winfo_children:
                # It's a container, so iterate through its children
                for w in widget.winfo_children():
                    # change its state
                    w.state((state,))
                    # and then recurse to process ITS children
                    cstate(w)

        cstate(self)

    def disable(self):
        self.enable("disabled")

# Credit: crxguy52, Stevoisiak, vegaseat, Victor Zaccardo @ https://stackoverflow.com/a/36221216
class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """

    def __init__(self, widget, text="widget info"):
        self.waittime = 500  # miliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(
            self.tw,
            text=self.text,
            justify="left",
            background="#ffffff",
            relief="solid",
            borderwidth=1,
            wraplength=self.wraplength,
        )
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

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
        list_ = [(self.set(k, column), k) for k in self.get_children("")]
        list_.sort(key=lambda t: data_type(t[0]), reverse=reverse)
        for index, (_, k) in enumerate(list_):
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

    def bind(self, *args, **kwargs):
        self.treeview.bind(*args, **kwargs)

    def __getattr__(self, name):
        # Pass all calls to the treeview
        if name == "treeview":
            # If this is not here it will recur infinitely
            raise AttributeError()
        return getattr(self.treeview, name, None)