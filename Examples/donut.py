import tkinter
from tkml import TKMLWidgetBuilder

root = tkinter.Tk()
TKMLWidgetBuilder().build_tkml_from_file(root, "./donut.xml")
root.mainloop()
