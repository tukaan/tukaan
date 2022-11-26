import tukaan
from tukaan._tcl import Tcl

app = None
window = None


def update():
    Tcl.call(None, "update")


def with_app_context(func):
    def wrapper():
        global app
        global window

        if app is None and window is None:
            app = tukaan.App("Test App")
            window = tukaan.MainWindow("Test window")

        func(app, window)

    return wrapper
