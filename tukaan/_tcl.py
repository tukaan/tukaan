from __future__ import annotations

import collections
import sys
import traceback
from numbers import Real
from pathlib import Path
from typing import Any, Callable, Type

import _tkinter as tk

from ._utils import _commands, counts, flatten, seq_pairs
from .exceptions import AppError, TclError

_tcl_interp = None


class Tcl:
    interp_address = None
    windowing_system = None
    version = None
    
    def __init__(self) -> None:
        global _tcl_interp

        if _tcl_interp is not None:
            raise AppError("can't create multiple Tcl interpreter.")
        
        _tcl_interp = tk.create(None, sys.argv[0], "Tukaan", False, False, True, False, None)
        _tcl_interp.loadtk()

        Tcl.interp_address = _tcl_interp.interpaddr()  # PIL needs this
        Tcl.windowing_system = _tcl_interp.call("tk", "windowingsystem").lower()
        Tcl.version = _tcl_interp.call("info", "patchlevel")

    @staticmethod
    def get_interp() -> tk.tkapp:
        if _tcl_interp is None:
            Tcl()
            
        return _tcl_interp

    @staticmethod
    def from_(type_spec: Type[Any], value: str | tk.Tcl_obj) -> Any:
        if type_spec is None:
            return None

        if type_spec is str:
            return Tcl.get_str(value)

        if type_spec is bool:
            if not Tcl.from_(str, value):
                return None

            return Tcl.get_bool(value)

        if type_spec is int or type_spec is float:
            return Tcl.get_number(type_spec, value)

        if hasattr(type_spec, "_from__tcl__"):
            return type_spec._from__tcl__(value)

        if isinstance(type_spec, (list, tuple, dict)):
            items = Tcl.get_list(value)

            if isinstance(type_spec, list):
                return [Tcl.from_(type_spec[0], item) for item in items]

            if isinstance(type_spec, tuple):
                if len(type_spec) != len(items):
                    type_spec *= len(items)
                return tuple(map(Tcl.from_, type_spec, items))

            if isinstance(type_spec, dict):
                result = {}
                for key, value in seq_pairs(items):
                    result[str(key)] = Tcl.from_(type_spec.get(key, str), value)
                    
                return result

        if type_spec is Path:
            return Path(value).resolve()

    @staticmethod
    def to(value: Any) -> str | tuple | tk.Tcl_Obj:
        if isinstance(value, (str, tk.Tcl_Obj)):
            return value

        if value is None:
            return ""

        if isinstance(value, bool):
            return "1" if value else "0"

        if isinstance(value, Real):
            return str(value)

        if hasattr(value, "_name"):
            return value._name

        if hasattr(value, "__to_tcl__"):
            return value.__to_tcl__()

        if isinstance(value, collections.abc.Mapping):
            return tuple(map(Tcl.to, flatten(value.items())))

        if callable(value):
            return Tcl.create_cmd(value)

        if isinstance(value, Path):
            return str(value.resolve())

        try:
            return tuple(map(Tcl.to, value))
        except TypeError:
            raise TypeError("can't convert object to Tcl. Please provide a __to_tcl__ method.")

    @staticmethod
    def call(return_type: Any, *args) -> Any:
        try:
            result = _tcl_interp.call(*map(Tcl.to, args))
            if return_type is None:
                return
            return Tcl.from_(return_type, result)

        except tk.TclError as e:
            msg = str(e)

            if "application has been destroyed" in msg:
                raise AppError("can't invoke Tcl callback. Application has been destroyed.")

            if msg.startswith("couldn't read file"):
                # FileNotFoundError is a bit more pythonic than TclError: couldn't read file
                path = msg.split('"')[1]  # path is between ""
                sys.tracebacklimit = 0
                raise FileNotFoundError(f"No such file or directory: {path!r}") from None
            else:
                raise TclError(msg) from None

    @staticmethod
    def eval(return_type: Any, script: str) -> Any:
        try:
            result = _tcl_interp.eval(script)
        except tk.TclError as e:
            raise TclError(str(e))
        else:
            return Tcl.from_(return_type, result)

    @staticmethod
    def create_cmd(func: Callable, *, args=(), kwargs={}) -> str:
        name = f"tukaan_command_{next(counts['commands'])}"
        _commands[name] = func

        def real_func(*tcl_callback_args):
            try:
                return func(*tcl_callback_args, *args, **kwargs)
            except Exception:
                # remove unnecessary lines:
                # File "/home/.../_utils.py", line 88, in real_func
                # return func(*args)
                tb = traceback.format_exc().split("\n")[3:]
                print("Traceback (most recent call last):\n", "\n".join(tb))

        _tcl_interp.createcommand(name, real_func)
        return name

    @staticmethod
    def delete_cmd(name: str) -> None:
        _tcl_interp.deletecommand(name)
        del _commands[name]

    @staticmethod
    def get_bool(obj) -> bool:
        return _tcl_interp.getboolean(obj)

    @staticmethod
    def get_str(obj) -> str:
        if isinstance(obj, str):
            return obj

        if isinstance(obj, tk.Tcl_Obj):
            return obj.string

        return _tcl_interp.call("format", obj)

    @staticmethod
    def get_number(type_spec: Type[int] | Type[float], value: str | tk.Tcl_obj) -> float | None:
        if not Tcl.get_str(value):
            return None
        
        return type_spec(_tcl_interp.getdouble(value))

    @staticmethod
    def get_list(obj) -> tuple:
        return _tcl_interp.splitlist(obj)

    @staticmethod
    def main_loop() -> None:
        _tcl_interp.mainloop(0)

    @staticmethod
    def quit_interp() -> None:
        global _tcl_interp
        _tcl_interp.quit()
        _tcl_interp = None

    def to_tcl_args(**kwargs) -> tuple:
        result = []

        for key, value in kwargs.items():
            if value is None:
                continue

            if key.endswith("_"):
                key = key.rstrip("_")

            result.extend([f"-{key}", value])

        return tuple(result)

    @staticmethod
    def updated(func: Callable) -> Callable:
        def wrapper(self, *args, **kwargs) -> Any:
            _tcl_interp.eval("update idletasks")
            result = func(self, *args, **kwargs)
            _tcl_interp.eval("update idletasks")
            return result
        return wrapper

    @staticmethod
    def update_before(func: Callable) -> Callable:
        def wrapper(self, *args, **kwargs) -> Any:
            _tcl_interp.eval("update idletasks")
            return func(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def update_after(func: Callable) -> Callable:
        def wrapper(self, *args, **kwargs) -> Any:
            result = func(self, *args, **kwargs)
            _tcl_interp.eval("update idletasks")
            return result
        return wrapper
