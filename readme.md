# Python-TKML
### Example Simple Calculator XML
```xml
<!-->Save this file as "calculator.xml"<-->
<Frame layout="V">
    <Geometry>200x180</Geometry>
    <Style font="Arial, 18">TButton</Style>
    <Label text="Calculator Example" />
    <Frame layout="V" inline_style="background=white;">
        <String id="buffer" />
        <Label textvariable="buffer" inline_style="background=white;" />
    </Frame>
    <Frame layout="Grid">
        <RowConfigure weight="1">0</RowConfigure>
        <RowConfigure weight="1">1</RowConfigure>
        <RowConfigure weight="1">2</RowConfigure>
        <RowConfigure weight="1">3</RowConfigure>
        <ColumnConfigure weight="1">0</ColumnConfigure>
        <ColumnConfigure weight="1">1</ColumnConfigure>
        <ColumnConfigure weight="1">2</ColumnConfigure>
        <ColumnConfigure weight="1">3</ColumnConfigure>
        <Row>
            <Button text="1" command="enter_1" />
            <Button text="2" command="enter_2" />
            <Button text="3" command="enter_3" />
            <Button text="+" command="enter_add" />
        </Row>
        <Row>
            <Button text="4" command="enter_4" />
            <Button text="5" command="enter_5" />
            <Button text="6" command="enter_6" />
            <Button text="-" command="enter_sub" />
        </Row>
        <Row>
            <Button text="7" command="enter_7" />
            <Button text="8" command="enter_8" />
            <Button text="9" command="enter_9" />
            <Button text="*" command="enter_mul" />
        </Row>
        <Row>
            <Button text="CLS" command="clear" />
            <Button text="0" command="enter_0" />
            <Button text="=" command="equals" />
            <Button text="/" command="enter_div" />
        </Row>
    </Frame>
</Frame>
```
### Example Simple Calculator Python
```python
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
```

## TKML usage
TKML works by passing the xml keywords to the tkinter widgets after converting them to usable values.
| XML Keyword | Converted Value | Example |
| ----------- | --------------- | ------- |
| command     | lambda: getattr(master, command)() | command="add_one"
| columns     | list | columns="id, name, stock, unit"
| id          | master._tkml_variables[id] = current_widget | id="my_string_var"
| textvariable | master._tkml_variables[textvariable] | textvariable="my_string_var"
| * | if attribute is all numbers then convert attribute to int | width="100" becomes width=100

TKML adds some more features. All Frames are set to expand=1 and fill="both" by default. Grid automatically handles row and column even with compilicated layouts using rowspan and columnspan. Support for inline_styles.