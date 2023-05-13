from __future__ import annotations

import collections.abc
from enum import Enum
from inspect import isclass
from numbers import Real
from pathlib import Path
from typing import Any, Callable, NoReturn, TypeAlias, Union, overload, Iterable

# Yes, we use _tkinter, because it "just works"
# I do plan to write our own _tkinter.c though, so `to` and `from_` can be optimized more
import _tkinter as tk

from tukaan._system import Platform, Version
from tukaan._typing import T, T_co, T_contra
from tukaan.errors import AppDoesNotExistError, TclCallError

TclValue: TypeAlias = Union[Real, str, bool, tk.Tcl_Obj]


class Tcl:
    _interp: tk.TkappType
    interp_address: int | None = None

    @classmethod
    def initialize(cls, app_name: str, screen_name: str | None) -> None:
        """Initialize the Tcl interpreter."""
        app_name = app_name.capitalize().replace(" ", "_")
        cls._interp = interp = tk.create(
            screen_name,  # screenName, $DISPLAY by default
            "",  # baseName, ignored in _tkinter.c
            app_name,  # className, the classname of the main window
            False,  # not interactive
            False,  # wantobjects, we don't want _tkinter to convert Tcl stuff to Python, because it's SLOW
            True,  # wantTk
            False,  # sync, don't execute X commands synchronously
            None,  # use, we don't want to embed the root window
        )
        interp.loadtk()
        interp.call("wm", "withdraw", ".")

        cls.interp_address = interp.interpaddr()  # PIL needs this

        Platform.tcl_version = cls.call(Version, "set", "tcl_patchLevel")
        Platform.tk_version = cls.call(Version, "set", "tk_patchLevel")
        Platform.window_sys = str(interp.call("tk", "windowingsystem")).lower()
        Platform.dll_ext = str(interp.call("info", "sharedlibextension"))

    @classmethod
    def main_loop(cls) -> None:
        """Start the main event loop."""
        cls._interp.mainloop(0)

    @classmethod
    def quit(cls) -> None:
        """Quit the interpreter."""
        cls._interp.quit()

    @classmethod
    def load_dll(cls, dll_path: Path, pkg_name: str | None) -> None:
        """Load a Tcl extension package from a DLL (.dll, .dylib or .so file)"""
        cls._interp.call("load", str(dll_path.resolve().absolute()), pkg_name)

    # Converter methods

    @overload
    @staticmethod
    def to(
        obj: Iterable[Any] | collections.abc.Mapping[Any, Any]
    ) -> tuple[TclValue, ...]:
        ...

    @overload
    @staticmethod
    def to(obj: TclValue | bool | Real | Callable[..., Any] | Enum | Path) -> str:
        ...

    @staticmethod
    def to(obj: Any) -> TclValue | tuple[TclValue, ...]:
        if isinstance(obj, (str, bool, Real, tk.Tcl_Obj)):
            value = obj
        elif isinstance(obj, (tuple, list, set)):
            return tuple(Tcl.to(item) for item in obj)
        elif hasattr(obj, "_name"):
            value = obj._name
        elif hasattr(obj, "__to_tcl__"):
            value = obj.__to_tcl__()
        elif isinstance(obj, dict):
            value = tuple(Tcl.to(item) for pair in obj.items() for item in pair)
        elif isinstance(obj, Path):
            value = str(obj.resolve().absolute())
        elif isinstance(obj, Enum):
            value = Tcl.to(obj.value)
        else:
            try:
                iter(obj)
            except TypeError:
                raise TypeError(
                    f"cannot convert {obj!r} to Tcl. Please provide a `__to_tcl__` method."
                ) from None
            else:
                value = tuple(Tcl.to(o) for o in obj)
        return value

    @staticmethod
    def from_(type_spec: Any, value: TclValue) -> Any:
        if isclass(type_spec) and isinstance(value, type_spec):
            return value
        elif type_spec is bool:
            return Tcl._interp.getboolean(value)
        elif type_spec is int:
            return Tcl._interp.getint(value)
        elif type_spec is float:
            return Tcl._interp.getdouble(value)
        elif isinstance(type_spec, type):
            if hasattr(type_spec, "__from_tcl__"):
                return type_spec.__from_tcl__(value)  # type: ignore
            elif issubclass(type_spec, Enum):
                return type_spec(value)
            elif issubclass(type_spec, Path):
                return Path(Tcl.from_(str, value)).resolve()

        elif isinstance(type_spec, (set, list, tuple, dict)):
            sequence = Tcl._interp.splitlist(value)

            if isinstance(type_spec, (set, list)):
                # {int} -> {1, 2, 3}
                # [int] -> [1, 2, 3]
                [items_type] = type_spec
                return type(type_spec)(Tcl.from_(items_type, item) for item in sequence)
            elif isinstance(type_spec, tuple):
                # (int, str) -> (1, "spam", "str")
                diff = len(sequence) - len(type_spec)
                if diff:
                    type_spec = type_spec + (type_spec[-1],) * diff
                return tuple(map(Tcl.from_, type_spec, sequence))
            elif isinstance(type_spec, dict):
                # {"a": int, "b": str} -> {"a": 1, "b": "spam", "c": "str"}
                return {
                    str(k): Tcl.from_(type_spec.get(k, str), v)
                    for k, v in zip(sequence[::2], sequence[1::2])
                }

        elif type_spec is str:
            if isinstance(value, tk.Tcl_Obj):
                return str(value.string)
            return Tcl.from_(str, Tcl._interp.call("format", value))

        raise TypeError(
            f"cannot convert Tcl value to Python: {value!r}. Invalid return type specification: {type_spec!r}"
        ) from None

    # Tcl interface

    @overload
    @classmethod
    def call(cls, return_type: None, *args: Any) -> None:
        ...

    @overload
    @classmethod
    def call(cls, return_type: type[T] | T, *args: Any) -> T:
        ...

    @classmethod
    def call(cls, return_type: type[T] | T | None, *args: Any) -> T | None:
        try:
            result = cls._interp.call(*[cls.to(arg) for arg in args])
        except tk.TclError as e:
            Tcl.raise_error(e)
        else:
            return None if return_type is None else cls.from_(return_type, result)

    @overload
    @classmethod
    def eval(cls, return_type: None, script: str) -> None:
        ...

    @overload
    @classmethod
    def eval(cls, return_type: type[T] | T, script: str) -> T:
        ...

    @classmethod
    def eval(cls, return_type: type[T] | T | None, script: str) -> T | None:
        try:
            result = cls._interp.eval(script)
        except tk.TclError as e:
            Tcl.raise_error(e)
        else:
            return None if return_type is None else cls.from_(return_type, result)

    @staticmethod
    def raise_error(error: tk.TclError) -> NoReturn:
        message = str(error)
        if "has been destroyed" in message or "NULL main window" in message:
            raise AppDoesNotExistError("application has been destroyed.") from None
        elif "no such file or directory" in message:
            filename = message.split('"')[1]
            raise FileNotFoundError(f"No such file or directory: {filename!r}") from None
        raise TclCallError(message) from None

    @staticmethod
    def to_tcl_args(**kwargs: Any) -> tuple[Any, ...]:
        result: list[Any] = []
        for key, value in kwargs.items():
            if value is None:
                continue

            if key.endswith("_"):
                key = key.rstrip("_")

            result.extend((f"-{key}", value))
        return tuple(result)
