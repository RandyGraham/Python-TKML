import tkinter as tk
from tkml import TKMLWidget


class Calculator(TKMLWidget):
    def __init__(self, parent):
        super().__init__(parent)

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

    def equals(self):
        self["buffer"].set(eval(self["buffer"].get()))

    def clear(self):
        self["buffer"].set("")


root = tk.Tk()
calc = Calculator(root)
calc.build_tkml_from_file("./calculator.xml")
calc.pack()
root.mainloop()