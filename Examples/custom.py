import tkinter as tk
import tkinter.ttk as ttk
import tkml
import webbrowser


class BlogPost(ttk.Frame):
    def __init__(self, parent, author, title, text):
        super().__init__(parent)
        self.parent = parent
        self.author = author
        self.title = title
        self.text = text
        ttk.Label(self, text=self.title).pack()
        ttk.Label(self, text=f"Authored by {self.author}").pack()
        self.text = tk.Text(self)
        self.text.insert("1.0", text)
        self.text.configure(state="disabled")
        self.text.pack()


def open_browser(tkml_widget_builder, master, node, parent):
    url = node.attrib["url"]
    webbrowser.open_new(url)


def diagonal_layout(tkml_widget_builder, master, node, parent):
    index = 0
    for child in node:
        layout_attributes = tkml.pull_layout_attributes(child)
        child_widget = tkml_widget_builder._handle_any(master, child, parent)
        if child_widget is None:
            continue
        child_widget.grid(row=index, column=index)
        index += 1
    return parent


widget_builder = tkml.TKMLWidgetBuilder()
widget_builder.add_layout("diagonal", diagonal_layout)
widget_builder.add_command("Browser-Open", open_browser)
widget_builder.add_terminal("BlogPost", BlogPost)

root = tk.Tk()
widget_builder.build_tkml_from_file(root, "./custom.xml")
root.mainloop()
