# The super().__init__(errormsg) initializes the Exception object and returns an error with custom message (errormsg). Call it like this: raise AppError("Hello, World: There was an error"

# Displayed like this:

# Traceback (most recent call last):
#   File "/file/path/", line 5, in <module>
#     raise AppError("Hello, World: There was an error")
# AppError: Hello, World: There was an error

class TclError(Exception):
    def __init__(self, errormsg):
        self.errormsg = errormsg
        super().__init__(errormsg)


class AppError(Exception):
    def __init__(self, errormsg):
        self.errormsg = errormsg
        super().__init__(errormsg)


class WidgetError(Exception):
    def __init__(self, errormsg):
        self.errormsg = errormsg
        super().__init__(errormsg)


class ColorError(Exception):
    def __init__(self, errormsg):
        self.errormsg = errormsg
        super().__init__(errormsg)


class FontError(Exception):
    def __init__(self, errormsg):
        self.errormsg = errormsg
        super().__init__(errormsg)


class LayoutError(Exception):
    def __init__(self, errormsg):
        self.errormsg = errormsg
        super().__init__(errormsg)


class CellNotFoundError(LayoutError):
    def __init__(self, errormsg):
        self.errormsg = errormsg
        super().__init__(errormsg)
