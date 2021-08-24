import platform
import _tkinter as tk

from .utils import ClassPropertyMetaClass, classproperty, get_tcl_interp


class Platform(metaclass=ClassPropertyMetaClass):
    version = platform.version()
    node = platform.node()
    processor = platform.processor()
    machine = platform.machine()
    release = platform.release()
    system = platform.system()
    arch = platform.architecture()

    @classproperty
    def windowing_system(cls):
        return get_tcl_interp().tcl_call(str, "tk", "windowingsystem")

    @classproperty
    def tcl_version(cls):
        return get_tcl_interp().tcl_call(str, "info", "patchlevel")

    @classproperty
    def tk_version(cls):
        return float(tk.TK_VERSION)