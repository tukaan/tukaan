# The super().__init__(errormsg) initializes the Exception object and returns an error with custom message (errormsg). Call it like this: raise AppError("Hello, World: There was an error"

# Displayed like this:

# Traceback (most recent call last):
#   File "/file/path/", line 5, in <module>
#     raise AppError("Hello, World: There was an error")
# AppError: Hello, World: There was an error

class TclError(Exception):
    def __init__(self, errormsg="There was an error rendering or initializing TCL"):
        self.errormsg = errormsg
        super().__init__(errormsg)


class AppError(Exception):
    def __init__(self, errormsg="There was an error rendering the app"):
        self.errormsg = errormsg
        super().__init__(errormsg)


class WidgetError(Exception):
    def __init__(self, errormsg="There was an error rendering a widget"):
        self.errormsg = errormsg
        super().__init__(errormsg)


class ColorError(Exception):
    def __init__(self, errormsg=="There was an error finding color"):
        self.errormsg = errormsg
        super().__init__(errormsg)


class FontError(Exception):
    def __init__(self, errormsg=="There was an error rendering the font"):
        self.errormsg = errormsg
        super().__init__(errormsg)


class LayoutError(Exception):
    def __init__(self, errormsg=="There was an error rendering getting the layout"):
        self.errormsg = errormsg
        super().__init__(errormsg)


class CellNotFoundError(LayoutError):
    def __init__(self, errormsg="There was an error finding the specified cell"):
        self.errormsg = errormsg
        super().__init__(errormsg)
