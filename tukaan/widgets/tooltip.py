from tukaan import Label

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
        if self.orient == "N":
            self.tooltip.layout.position(x=self.widget.rel_x, y=int(self.widget.rel_y-self.tooltip.height-5))
        elif self.orient == "E":
            self.tooltip.layout.position(x=int(self.widget.abs_x+self.widget.width+5), y=self.widget.rel_y)
        elif self.orient == "S":
            self.tooltip.layout.position(x=self.widget.rel_x, y=int(self.widget.rel_y+self.widget.height+5))
        elif self.orient == "W":
            self.tooltip.layout.position(x=int(self.widget.abs_x-self.tooltip.width-5), y=self.widget.rel_y)
        elif self.orient == "NE":
            self.tooltip.layout.position(x=int(self.widget.abs_x+self.widget.width+5), y=int(self.widget.rel_y-self.tooltip.height-5))
        elif self.orient == "SE":
            self.tooltip.layout.position(x=int(self.widget.abs_x+self.widget.width+5), y=int(self.widget.rel_y+self.widget.height+5))
        elif self.orient == "NW":
            self.tooltip.layout.position(x=int(self.widget.abs_x-self.tooltip.width-5), y=int(self.widget.rel_y-self.tooltip.height-5))
        elif self.orient == "SW":
            self.tooltip.layout.position(x=int(self.widget.abs_x-self.tooltip.width-5), y=int(self.widget.rel_y+self.widget.height+5))
    
    def leave(self, *args):
        self.tooltip.destroy()
