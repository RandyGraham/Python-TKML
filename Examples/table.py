from tkml import TKMLDriver, TKMLTopLevelDriver, TKMLWidgetBuilder
import random
import tkinter as tk

widget_builder = TKMLWidgetBuilder()

food_descriptors = [
    "Hot",
    "Cold",
    "Gooey",
    "Chocolatey",
    "Spicy",
    "Sweet",
    "Mashed",
    "Minced",
    "Super",
    "Candied",
]
food_nouns = ["Cookie", "Cake", "Hot Dog", "Steak", "Potatoes", "Milkshake"]


class Popup(TKMLTopLevelDriver):
    def __init__(self, food_count):
        super().__init__()
        self.food_count = tk.IntVar(value=food_count)


class TableExample(TKMLDriver):
    def __init__(self, parent):
        super().__init__(parent)
        self.food_count = tk.IntVar()

    def add_random(self):
        self["example_table"].insert(
            "",
            tk.END,
            values=(
                random.choice(food_descriptors) + " " + random.choice(food_nouns),
                random.randint(120, 800),
                f"{random.randint(1,10)}/10",
            ),
        )
        self.food_count.set(len(self["example_table"].get_children()))

    def select_all(self):
        for item in self["example_table"].get_children():
            self["example_table"].selection_add(item)

    def remove_selected(self):
        for item in self["example_table"].selection():
            self["example_table"].delete(item)
        self.food_count.set(len(self["example_table"].get_children()))

    def checkout(self):
        toplevel = Popup(self.food_count.get())
        widget_builder.build_tkml_from_file(toplevel, "./table_popup.xml")


root = tk.Tk()
table_example = TableExample(root)
widget_builder.build_tkml_from_file(table_example, "./table.xml")
table_example.pack()
root.mainloop()
