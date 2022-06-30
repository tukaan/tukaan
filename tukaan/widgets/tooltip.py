from tukaan import Label
from tukaan._tcl import Tcl

class ToolTip():
    def __init__(self, window, widget=None, orient="E", *args, **kwargs):
        try:
            self.text = kwargs.pop("text")
        except:
            raise Exception("No text provided for ToolTip")
        self.window = window
        self.widget = widget
        self.orient=orient
        self.widget.bind("<MouseEnter>", self.enter)
        self.widget.bind("<MouseLeave>", self.leave)
        self.widget.bind("<MouseDown>", self.leave)

    def enter(self, *args):
        self.tooltip = Label(self.window, text=self.text)
        Tcl.call(None, self.tooltip, "configure", "-relief", "solid")
        Tcl.call(None, self.tooltip, "configure", "-borderwidth", "1")
        X = self.widget.rel_x
        Y = self.widget.rel_y
        NY = int(self.widget.rel_y-self.tooltip.height-5)
        EX = int(self.widget.abs_x+self.widget.width+5)
        SY = int(self.widget.rel_y+self.widget.height+5)
        WX = int(self.widget.abs_x-self.tooltip.width-5)
        if self.orient == "N":
            self.tooltip.layout.position(x=X, y=NY)
        elif self.orient == "E":
            self.tooltip.layout.position(x=EX, y=Y)
        elif self.orient == "S":
            self.tooltip.layout.position(x=X, y=SY)
        elif self.orient == "W":
            self.tooltip.layout.position(x=WX, y=Y)
        elif self.orient == "NE":
            self.tooltip.layout.position(x=EX, y=NY)
        elif self.orient == "SE":
            self.tooltip.layout.position(x=EX, y=SY)
        elif self.orient == "NW":
            self.tooltip.layout.position(x=WX, y=NY)
        elif self.orient == "SW":
            self.tooltip.layout.position(x=WX, y=SY)
    
    def leave(self, *args):
        self.tooltip.destroy()
