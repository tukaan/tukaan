from __future__ import annotations

import collections.abc
import sys
from enum import Enum, EnumMeta
from inspect import isclass
from itertools import chain
from numbers import Real
from pathlib import Path
from traceback import format_exc
from typing import Any, Callable, NoReturn, TypeAlias, Union, overload

import _tkinter as tk

# Yes, we use _tkinter, because it "just works"
# I do plan to write our own _tkinter.c though, so it can be optimized more

from ._typing import T, T_co, T_contra

TclValue: TypeAlias = Union[str, tk.Tcl_Obj]


class Tcl:
    _interp: tk.TkappType

    version: str
    interp_address: int
    windowing_system: str
    dll_ext: str

    @classmethod
    def initialize(cls, app_name: str, screen_name: str | None) -> None:
        """Initialize the Tcl interpreter."""
        cls._interp = interp = tk.create(screen_name, "", app_name, False, False, True, False, None)  # type: ignore
        interp.loadtk()
        #interp.call("wm", "withdraw", ".")

        cls.version = interp.call("info", "patchlevel")
        cls.interp_address = interp.interpaddr()  # PIL needs this # type: ignore
        cls.windowing_system = str(interp.call("tk", "windowingsystem")).lower()
        cls.dll_ext = interp.call("info", "sharedlibextension")

    @classmethod
    def start_main_loop(cls) -> None:
        """Start the main event loop."""
        cls._interp.mainloop(0)  # type: ignore

    @classmethod
    def quit(cls) -> None:
        """Quit the interpreter."""
        cls._interp.quit()  # type: ignore

    @classmethod
    def load_dll(cls, dll_path: Path, pkg_name: str | None) -> None:
        """Load a Tcl extension package from a DLL (.dll, .dylib or .so file)"""
        cls._interp.call("load", str(dll_path.resolve().absolute()), pkg_name)

    # Converter methods

    @overload
    @staticmethod
    def to(
        obj: collections.abc.Iterator[Any] | collections.abc.Mapping[Any, Any]
    ) -> tuple[TclValue, ...]:
        ...

    @overload
    @staticmethod
    def to(
        obj: TclValue | bool | numbers.Real | Callable[..., Any] | Enum | Path
    ) -> str:
        ...

    @staticmethod
    def to(obj: Any) -> TclValue | tuple[TclValue, ...]:
        if isinstance(obj, (str, bool, Real, tk.Tcl_Obj)):
            value = obj
        elif isinstance(obj, (tuple, list)):
            return tuple(Tcl.to(o) for o in obj)
        elif hasattr(obj, "_name"):
            value = obj._name
        elif hasattr(obj, "__to_tcl__"):
            value = obj.__to_tcl__()
        elif isinstance(obj, collections.abc.Mapping):
            value = tuple(map(Tcl.to, chain.from_iterable(obj.items())))
        elif callable(obj):
            value = Procedure(obj)._name
        elif isinstance(obj, Path):
            value = str(obj.resolve().absolute())
        elif isinstance(obj, Enum):
            value = Tcl.to(obj.value)
        else:
            try:
                iter(obj)
            except TypeError:
                raise TypeError(
                    "cannot convert Python object to Tcl. Please provide a `__to_tcl__` method."
                ) from None
            else:
                value = tuple(Tcl.to(o) for o in obj)

    @staticmethod
    def from_(return_type: Any, value: TclValue) -> Any:
        if isclass(return_type) and isinstance(value, return_type):
            return value

        elif return_type is bool:
            return Tcl._interp.getboolean(value)

        elif return_type in (int, float):
            return return_type(Tcl._interp.getdouble(value))

        elif hasattr(return_type, "__from_tcl__"):
            return return_type.__from_tcl__(value)

        elif isinstance(return_type, (set, list, tuple, dict)):
            sequence = Tcl._interp.splitlist(value)

            if isinstance(return_type, (set, list)):
                [items_type] = return_type
                return type(return_type)(
                    (Tcl.from_(items_type, item) for item in sequence)
                )

            if isinstance(return_type, tuple):
                diff = len(sequence) - len(return_type)
                if diff:
                    return_type = return_type + (return_type[-1],) * diff
                return tuple(map(Tcl.from_, return_type, sequence))

            if isinstance(return_type, dict):
                return {
                    str(k): Tcl.from_(return_type.get(k, str), v)
                    for k, v in zip(sequence[::2], sequence[1::2])
                }

        elif return_type is str:
            if isinstance(value, tk.Tcl_Obj):
                return str(value.string)

            return Tcl.from_(str, Tcl._interp.call("format", value))

        elif isinstance(return_type, EnumMeta):
            return return_type(value)

        elif return_type is Path:
            return Path(Tcl.from_(str, value)).resolve()

        assert False  # type-guard, sorta

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
            print(result)
        except tk.TclError as e:
            Tcl.raise_error(e)
        else:
            return None if return_type is None else cls.from_(return_type, result)

    @staticmethod
    def raise_error(error: tk.TclError) -> NoReturn:
        message = str(error)

        if "has been destroyed" in message or "NULL main window" in message:
            raise Exception("application has been destroyed.")

        if message.startswith("couldn't read file"):
            # FileNotFoundError is a bit more Pythonic
            sys.tracebacklimit = 0
            quote = '"'
            raise FileNotFoundError(
                f"No such file or directory: {message.split(quote)[1]!r}"
            ) from None

        raise Exception(message) from None

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


class Procedure:
    def __init__(self, callback: Callable[..., Any]) -> None:
        self._callback = callback
        self._name = name = "tukaan_command_"

        Tcl._interp.createcommand(name, self.__call__)  # type: ignore

    def __call__(self, *tcl_args: Any) -> Any:
        try:
            return self._callback(*tcl_args)
        except Exception:
            print("Exception in Tukaan callback:", format_exc(), sep="\n")

    def dispose(self, _name: str | None = None) -> None:
        Tcl._interp.deletecommand(_name)  # type: ignore
