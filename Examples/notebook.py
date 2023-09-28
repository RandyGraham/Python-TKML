from tkml import TKMLDriver, TKMLWidgetBuilder
import tkinter

root = tkinter.Tk()

TKMLWidgetBuilder().build_tkml_from_string(
    root,
    """
<Notebook>
    <Title>Notebook and build from string combo example</Title>
    <Geometry>400x400</Geometry>
    <Frame tabname="My First Tab">
        <Label text="hello from my first tab!"/>
    </Frame>
    <Frame tabname="My Second Tab">
        <Label text="hello from my second tab!"/>
    </Frame>
</Notebook>
""",
)

root.mainloop()
