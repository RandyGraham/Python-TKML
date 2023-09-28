import tkinter as tk
from tkml import TKMLDriver, TKMLWidgetBuilder


class Calculator(TKMLDriver):
    def __init__(self, parent):
        super().__init__(parent)
        self.paren_state = tk.StringVar(value="(")
        self.load_store_var = None

    def enter(self, value):
        self["buffer"].set(self["buffer"].get() + value)

    def __getattr__(self, name):
        if name.startswith("enter_") and name[-1].isdigit():
            return lambda: self.enter(name[-1])
        return AttributeError()

    def enter_mul(self):
        self.enter("*")

    def enter_div(self):
        self.enter("/")

    def enter_add(self):
        self.enter("+")

    def enter_sub(self):
        self.enter("-")

    def enter_dot(self):
        self.enter(".")

    def enter_paren(self):
        self.enter(self["paren"].get())
        self["paren"].set("(" if self["paren"].get() == ")" else ")")

    def load(self):
        if self.load_store_var is not None:
            self.enter(self.load_store_var)

    def store(self):
        self.load_store_var = self["buffer"].get()

    def equals(self):
        try:
            self["buffer"].set(eval(self["buffer"].get()))
        except Exception as e:
            self["buffer"].set("Error")

    def clear(self):
        self["buffer"].set("")


root = tk.Tk()
calc = Calculator(root)
TKMLWidgetBuilder().build_tkml_from_file(calc, "./calculator.xml")
calc.pack()
root.mainloop()
