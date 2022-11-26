from __future__ import annotations

import collections
import contextlib
import functools
import itertools
import numbers
import sys
import traceback
from enum import Enum, EnumMeta
from pathlib import Path
from typing import Any, Callable

import _tkinter as tk

from tukaan._collect import _commands, counter
from tukaan.exceptions import TukaanTclError


class TclCallback:
    def __init__(self, callback: Callable[..., Any], converters=(), args=(), kwargs={}):
        self._callback = callback
        self._converters = converters
        self._args = args
        self._kwargs = kwargs

        self._name = name = f"tukaan_command_{next(counter['commands'])}"
        _commands[name] = callback

        Tcl._interp.createcommand(name, self.__call__)

    def __call__(self, *tcl_args) -> Any:
        if self._converters and tcl_args:
            result = []
            for index, value in enumerate(tcl_args):
                with contextlib.suppress(KeyError):
                    value = Tcl.from_(self._converters[index], value)
                result.append(value)

            tcl_args = tuple(result)

        try:
            return self._callback(*tcl_args, *self._args, **self._kwargs)
        except Exception:
            # remove unnecessary lines:
            # File "/home/.../_tcl.py", line 46, in __call__
            # return func(*args)
            tb = traceback.format_exc().split("\n")[3:]
            print("Traceback (most recent call last):\n", "\n".join(tb))

    def dispose(self) -> None:
        Tcl._interp.deletecommand(self._name)
        del _commands[self._name]


class Tcl:
    """A Python interface to the Tcl interpreter."""

    _interp: tk.TkappType

    @classmethod
    def init(cls, app_name: str, screen_name: str | None) -> None:
        """Initialize the interpreter."""
        cls._interp = tk.create(screen_name, app_name, app_name, False, False, True, False, None)
        cls._interp.loadtk()
        cls._interp.call("wm", "withdraw", ".")

        cls.interp_address = cls._interp.interpaddr()  # PIL needs this
        cls.windowing_system = cls._interp.call("tk", "windowingsystem").lower()
        cls.version = cls._interp.call("info", "patchlevel")
        cls.dll_ext = cls._interp.call("info", "sharedlibextension")

        cls.alive = True

    @classmethod
    def main_loop(cls) -> None:
        """Start the main event loop."""
        cls._interp.mainloop(0)

    @classmethod
    def do_one_event(cls) -> None:
        cls._interp.dooneevent(tk.DONT_WAIT)
        if not cls.alive:
            raise TukaanTclError

    @classmethod
    def quit(cls) -> None:
        """Quit the interpreter."""
        cls._interp.quit()
        cls.alive = False

    @classmethod
    def load_dll(cls, path: Path, pkg_name: str | None) -> None:
        cls._interp.call("load", str(path.resolve().absolute()), pkg_name)

    @staticmethod
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
    def to(obj: object) -> str | tk.Tcl_Obj | tuple[str | tk.Tcl_Obj, ...]:  # noqa: CCR001
        if isinstance(obj, (str, tk.Tcl_Obj)):
            return obj

        if isinstance(obj, bool):
            return "1" if obj else "0"

        if isinstance(obj, numbers.Real):
            return str(obj)

        try:
            return obj._name  # EAFP
        except AttributeError:
            pass

        try:
            to_tcl = obj.__to_tcl__
        except AttributeError:
            pass
        else:
            return to_tcl()

        if isinstance(obj, collections.abc.Mapping):
            return tuple(map(Tcl.to, itertools.chain.from_iterable(obj.items())))  # type: ignore

        if callable(obj):
            return TclCallback(obj)._name

        if isinstance(obj, Path):
            return str(obj.resolve())

        if isinstance(obj, Enum):
            return str(obj.value)

        try:
            return tuple(map(Tcl.to, obj))  # type: ignore
        except TypeError:
            raise TypeError(
                "cannot convert Python object to Tcl. Please provide a __to_tcl__ method."
            ) from None

    @staticmethod
    def from_(return_type: type[object], value: str | tk.Tcl_Obj) -> Any:  # noqa: CCR001
        if return_type is str:
            return Tcl.get_string(value)

        if return_type is bool:
            return Tcl.get_bool(value)

        if return_type in (int, float):
            return Tcl.get_number(return_type, value)  # type: ignore

        try:
            from_tcl = return_type.__from_tcl__  # type: ignore
        except AttributeError:
            pass
        else:
            return from_tcl(value)

        if isinstance(return_type, (list, tuple, dict)):
            sequence = Tcl.get_iterable(value)

            if isinstance(return_type, list):
                return [Tcl.from_(return_type[0], item) for item in sequence]

            if isinstance(return_type, tuple):
                items_len = len(sequence)
                if len(return_type) != items_len:
                    return_type *= items_len
                return tuple(map(Tcl.from_, return_type, sequence))

            if isinstance(return_type, dict):
                result = {}
                for key, value in zip(sequence[::2], sequence[1::2]):
                    result[str(key)] = Tcl.from_(return_type.get(key, str), value)

                return result

        if isinstance(return_type, EnumMeta):
            return return_type(value)

        if return_type is Path:
            return Path(Tcl.get_string(value)).resolve()

        if return_type is None:
            return None

    @classmethod
    def call(cls, return_type: type[object] | None, *args) -> Any:
        try:
            result = cls._interp.call(*map(cls.to, args))
        except tk.TclError as e:
            msg = str(e)

            if "has been destroyed" in msg:
                return

            if not msg.startswith("couldn't read file"):
                raise TukaanTclError(msg) from None

            # FileNotFoundError is a bit more Pythonic
            sys.tracebacklimit = 0
            quote = '"'
            raise FileNotFoundError(f"No such file or directory: {msg.split(quote)[1]!r}") from None
        else:
            if return_type is None:
                return
            return cls.from_(return_type, result)

    @classmethod
    def eval(cls, return_type: type[object], script: str) -> Any:
        try:
            result = cls._interp.eval(script)
        except tk.TclError as e:
            raise TukaanTclError(str(e)) from None
        else:
            return cls.from_(return_type, result)

    @classmethod
    def get_string(cls, value: str | tk.Tcl_Obj) -> str:
        if isinstance(value, str):
            return value

        if isinstance(value, tk.Tcl_Obj):
            return str(value.string)

        return cls._interp.call("format", value)

    @classmethod
    def get_number(
        cls, type_spec: type[int] | type[float], value: str | tk.Tcl_Obj
    ) -> float | None:
        return type_spec(cls._interp.getdouble(value)) if cls.get_string(value) else None

    @classmethod
    def get_bool(cls, value: str | tk.Tcl_Obj) -> bool | None:
        return cls._interp.getboolean(value) if cls.get_string(value) else None

    @classmethod
    def get_iterable(cls, value: str | tk.Tcl_Obj) -> tuple:
        return cls._interp.splitlist(value)

    @classmethod
    def with_redraw(cls, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            cls._interp.eval("update idletasks")
            result = func(self, *args, **kwargs)
            cls._interp.eval("update idletasks")
            return result

        return wrapper

    @classmethod
    def redraw_before(cls, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            cls._interp.eval("update idletasks")
            return func(self, *args, **kwargs)

        return wrapper

    @classmethod
    def redraw_after(cls, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            result = func(self, *args, **kwargs)
            cls._interp.eval("update idletasks")
            return result

        return wrapper
