from tkml import TKMLWidget, TKMLTopLevel
import random
import tkinter as tk

food_descriptors = ["Hot", "Cold", "Gooey", "Chocolatey", "Spicy", "Sweet", "Mashed", "Minced", "Super", "Candied"]
food_nouns = ["Cookie", "Cake", "Hot Dog", "Steak", "Potatoes", "Milkshake"]

class Popup(TKMLTopLevel):
    def __init__(self, food_count):
        super().__init__()
        self.food_count = tk.IntVar(value=food_count)


class TableExample(TKMLWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.food_count = tk.IntVar()

    def add_random(self):
        self["example_table"].insert(
            "", 
            tk.END, 
            values=( 
                random.choice(food_descriptors) + " " + random.choice(food_nouns), 
                random.randint(120,800), 
                f"{random.randint(1,10)}/10" )
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
        toplevel.build_tkml_from_file("./table_popup.xml")

if __name__ == "__main__":
    root = tk.Tk()
    table_example = TableExample(root)
    table_example.build_tkml_from_file("./table.xml")
    table_example.pack()
    root.mainloop()