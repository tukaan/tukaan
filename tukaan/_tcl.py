from __future__ import annotations

import collections
import collections.abc
import contextlib
import functools
import itertools
import numbers
import sys
import traceback
from enum import Enum, EnumMeta
from inspect import isclass
from pathlib import Path
from typing import Any, Callable, Sequence, Union, cast, overload

import _tkinter as tk

from tukaan._collect import commands, counter
from tukaan._typing import P, T, TypeAlias, WrappedFunction
from tukaan._utils import instanceclassmethod
from tukaan.exceptions import AppError, TukaanTclError

TclValue: TypeAlias = Union[str, tk.Tcl_Obj]


class TclCallback:
    def __init__(
        self,
        callback: Callable[..., Any],
        converters: Sequence[Any] = (),
        args: Sequence[Any] = (),
        **kwargs: collections.abc.Mapping[Any, Any],
    ):
        self._callback = callback
        self._converters = converters
        self._args = args
        self._kwargs = kwargs

        self._name = name = f"tukaan_command_{next(counter['commands'])}"
        commands[name] = callback

        Tcl._interp.createcommand(name, self.__call__)  # type: ignore

    def __call__(self, *tcl_args: Any) -> Any:
        if self._converters and tcl_args:
            result: list[Any] = []
            for index, value in enumerate(tcl_args):
                with contextlib.suppress(KeyError):
                    value = Tcl.from_(self._converters[index], value)
                result.append(value)

            tcl_args = tuple(result)

        try:
            return self._callback(*tcl_args, *self._args, **self._kwargs)
        except Exception:
            print("Exception in Tukaan callback:")
            print(traceback.format_exc())

    @instanceclassmethod
    def dispose(self_or_cls, _name: str | None = None) -> None:
        _name = _name or self_or_cls._name
        Tcl._interp.deletecommand(_name)  # type: ignore
        del commands[_name]


class Tcl:
    """A Python interface to the Tcl interpreter."""

    _interp: tk.TkappType

    @classmethod
    def init(cls, app_name: str, screen_name: str | None) -> None:
        """Initialize the interpreter."""
        cls._interp = cast(
            tk.TkappType,
            tk.create(screen_name, "", app_name, False, False, True, False, None),  # type: ignore
            # arg #2 'baseName' is ignored in `_tkinter.c`
        )
        cls._interp.loadtk()
        cls._interp.call("wm", "withdraw", ".")

        cls.interp_address: int = cls._interp.interpaddr()  # PIL needs this # type: ignore
        cls.windowing_system = cast(str, cls._interp.call("tk", "windowingsystem")).lower()
        cls.version: str = cls._interp.call("info", "patchlevel")
        cls.dll_ext: str = cls._interp.call("info", "sharedlibextension")

        cls.alive = True

    @classmethod
    def main_loop(cls) -> None:
        """Start the main event loop."""
        cls._interp.mainloop(0)  # type: ignore

    @classmethod
    def do_one_event(cls) -> None:
        cls._interp.dooneevent(tk.DONT_WAIT)  # type: ignore
        if not cls.alive:
            raise TukaanTclError

    @classmethod
    def quit(cls) -> None:
        """Quit the interpreter."""
        cls._interp.quit()  # type: ignore
        cls.alive = False

    @classmethod
    def load_dll(cls, path: Path, pkg_name: str | None) -> None:
        cls._interp.call("load", str(path.resolve().absolute()), pkg_name)

    @staticmethod
    def to_tcl_args(**kwargs: Any) -> tuple[Any]:
        result: list[str] = []

        for key, value in kwargs.items():
            if value is None:
                continue

            if key.endswith("_"):
                key = key.rstrip("_")

            result.extend([f"-{key}", value])

        return tuple(result)

    @overload
    @staticmethod
    def to(obj: collections.abc.Iterator[Any]) -> tuple[TclValue, ...]:
        ...

    @overload
    @staticmethod
    def to(obj: TclValue) -> TclValue:
        ...

    @overload
    @staticmethod
    def to(
        obj: bool
        | numbers.Real
        | Callable[..., Any]
        | Enum
        | Path
        | collections.abc.Mapping[Any, Any]
    ) -> str:
        ...

    @staticmethod
    def to(obj: Any) -> TclValue | tuple[TclValue, ...]:  # noqa: CCR001
        if isinstance(obj, (str, tk.Tcl_Obj)):
            return obj

        if isinstance(obj, bool):
            return "1" if obj else "0"

        if isinstance(obj, numbers.Real):
            return str(obj)

        try:
            return obj._name
        except AttributeError:
            pass

        try:
            obj.__to_tcl__
        except AttributeError:
            pass
        else:
            return obj.__to_tcl__()

        if isinstance(obj, collections.abc.Mapping):
            return tuple(map(Tcl.to, itertools.chain.from_iterable(obj.items())))  # type: ignore

        if callable(obj):
            return TclCallback(obj)._name

        if isinstance(obj, Path):
            return str(obj.resolve().absolute())

        if isinstance(obj, Enum):
            return str(obj.value)

        try:
            iter(obj)
        except TypeError:
            raise TypeError(
                "cannot convert Python object to Tcl. Please provide a __to_tcl__ method."
            ) from None
        else:
            return tuple(Tcl.to(o) for o in obj)

    @staticmethod
    def from_(return_type: Any, value: TclValue) -> T:  # noqa: CCR001
        if isclass(return_type) and isinstance(value, return_type):
            return value

        if return_type is bool:
            if not value:
                return False
            return Tcl._interp.getboolean(value)

        if return_type in (int, float):
            return return_type(Tcl._interp.getdouble(value))

        try:
            return_type.__from_tcl__
        except AttributeError:
            pass
        else:
            return return_type.__from_tcl__(value)

        if isinstance(return_type, (list, tuple, dict)):
            sequence = Tcl._interp.splitlist(value)

            if isinstance(return_type, list):
                type_ = return_type[0]
                return [Tcl.from_(type_, item) for item in sequence]

            if isinstance(return_type, tuple):
                items_len = len(sequence)
                if len(return_type) != items_len:
                    return_type *= items_len
                return tuple(map(Tcl.from_, return_type, sequence))

            if isinstance(return_type, dict):
                return {
                    str(k): Tcl.from_(return_type.get(k, str), v)
                    for k, v in zip(sequence[::2], sequence[1::2])
                }

        if return_type is str:
            if isinstance(value, tk.Tcl_Obj):
                return str(value.string)

            return Tcl._interp.call("format", value)

        if isinstance(return_type, EnumMeta):
            return return_type(value)

        if return_type is Path:
            return Path(Tcl.from_(str, value)).resolve()

        assert False  # type-guard, sorta

    @staticmethod
    def raise_error(error):
        msg = str(error)

        if "has been destroyed" in msg or "NULL main window" in msg:
            raise AppError("application has been destroyed.")

        if not msg.startswith("couldn't read file"):
            raise TukaanTclError(msg) from None

        # FileNotFoundError is a bit more Pythonic
        sys.tracebacklimit = 0
        quote = '"'
        raise FileNotFoundError(f"No such file or directory: {msg.split(quote)[1]!r}") from None

    @overload
    @classmethod
    def call(cls, return_type: None, *args: Any) -> None:
        ...

    @overload
    @classmethod
    def call(cls, return_type: type[T], *args: Any) -> T:
        ...

    @classmethod
    def call(cls, return_type: type[T] | None, *args: Any) -> T | None:
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
    def eval(cls, return_type: type[T], script: str) -> T:
        ...

    @classmethod
    def eval(cls, return_type: Any, script: str) -> Any:
        try:
            result = cls._interp.eval(script)
        except tk.TclError as e:
            Tcl.raise_error(e)
        else:
            if return_type is None:
                return
            return cls.from_(return_type, result)

    @classmethod
    def with_redraw(cls, func: WrappedFunction[P, T]):
        @functools.wraps(func)
        def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> T:
            cls._interp.eval("update idletasks")
            result = func(self, *args, **kwargs)
            cls._interp.eval("update idletasks")
            return result

        return wrapper

    @classmethod
    def redraw_before(cls, func: WrappedFunction[P, T]):
        @functools.wraps(func)
        def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> T:
            cls._interp.eval("update idletasks")
            return func(self, *args, **kwargs)

        return wrapper

    @classmethod
    def redraw_after(cls, func: WrappedFunction[P, T]):
        @functools.wraps(func)
        def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> T:
            result = func(self, *args, **kwargs)
            cls._interp.eval("update idletasks")
            return result

        return wrapper
