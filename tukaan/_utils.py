from __future__ import annotations

import collections
import collections.abc
import itertools
import numbers
import traceback
from pathlib import Path
from inspect import isclass
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Iterator

from .exceptions import TclError

if TYPE_CHECKING:
    from PIL import Image

    from ._base import TkWidget
    from ._images import Icon, _image_converter_class
    from ._variables import _TclVariable
    from .timeout import Timeout


class count:
    """Simplified itertools.count"""

    def __init__(self, start: int = 0) -> None:
        self._count = start

    def __next__(self) -> int:
        self._count += 1
        return self._count

    def __iter__(self) -> Iterator[int]:
        # function only for mypy
        yield self._count

    def __int__(self) -> int:
        return self._count


counts: DefaultDict[Any, Iterator[int]] = collections.defaultdict(lambda: count())


_callbacks: dict[str, Callable] = {}
_images: dict[str, _image_converter_class] = {}
_pil_images: dict[str, Image] = {}
_icons: dict[str, Icon] = {}
_timeouts: dict[str, Timeout] = {}
_variables: dict[str, _TclVariable] = {}
_widgets: dict[str, TkWidget] = {}


def updated(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        get_tcl_interp()._tcl_call(None, "update", "idletasks")
        result = func(self, *args, **kwargs)
        get_tcl_interp()._tcl_call(None, "update", "idletasks")
        return result

    return wrapper


def update_before(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        get_tcl_interp()._tcl_call(None, "update", "idletasks")
        return func(self, *args, **kwargs)

    return wrapper


def update_after(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        result = func(self, *args, **kwargs)
        get_tcl_interp()._tcl_call(None, "update", "idletasks")
        return result

    return wrapper


def reversed_dict(dictionary: dict) -> dict:
    return {value: key for key, value in dictionary.items()}


def get_tcl_interp():
    from .app import App, tcl_interp

    if tcl_interp is None:
        try:
            tcl_interp = App()
        except Exception as e:
            raise TclError(e)

    return tcl_interp


_flatten = itertools.chain.from_iterable


def create_command(func) -> str:
    name = f"tukaan_command_{next(counts['commands'])}"
    _callbacks[name] = func

    def real_func(*args):
        try:
            return func(*args)
        except Exception:
            # remove unnecessary lines:
            # File "/home/.../_utils.py", line 88, in real_func
            # return func(*args)
            tb = traceback.format_exc().split("\n")[3:]
            print("Traceback (most recent call last):", "\n".join(tb), sep="\n")

    get_tcl_interp().app.createcommand(name, real_func)
    return name


def delete_command(name: str) -> None:
    del _callbacks[name]
    get_tcl_interp().app.deletecommand(name)


def py_to_tcl_arguments(**kwargs) -> tuple:
    result = []

    for key, value in kwargs.items():
        if value is None:
            continue

        if key.endswith("_"):
            key = key.rstrip("_")

        result.extend([f"-{key}", value])

    return tuple(result)


def _pairs(sequence):
    """Source: https://github.com/Akuli/teek/blob/master/teek/_tcl_calls.py"""
    return zip(sequence[0::2], sequence[1::2])


def from_tcl(type_spec, value) -> Any:
    """Based on https://github.com/Akuli/teek/blob/master/teek/_tcl_calls.py"""
    if type_spec is None:
        return None

    if type_spec is str:
        return get_tcl_interp().get_string(value)

    if type_spec is bool:
        if not from_tcl(str, value):
            return None

        return get_tcl_interp().get_boolean(value)

    if type_spec is int:
        if value == "":
            return None
        return int(value)

    if isinstance(type_spec, type):
        if issubclass(type_spec, numbers.Real):
            string = from_tcl(str, value)
            if not string:
                return None

            return type_spec(string)  # type: ignore

        if hasattr(type_spec, "from_tcl"):
            string = from_tcl(str, value)

            if not string:
                return None

            return type_spec.from_tcl(string)  # type: ignore

    if isinstance(type_spec, (list, tuple, dict)):
        items = get_tcl_interp().split_list(value)

        if isinstance(type_spec, list):
            # [int] -> [1, 2, 3]
            (item_spec,) = type_spec
            return [from_tcl(item_spec, item) for item in items]

        if isinstance(type_spec, tuple):
            # (int, str) -> (1, 'hello')
            # if all type is same, can shorten:
            # (str) -> ('1', 'hello')
            if len(type_spec) != len(items):
                type_spec *= len(items)
            return tuple(map(from_tcl, type_spec, items))

        if isinstance(type_spec, dict):
            # {'a': int, 'b': str} -> {'a': 1, 'b': 'hello', 'c': 'str assumed'}
            result = {}
            for key, value in _pairs(items):
                key = from_tcl(str, key)
                result[key] = from_tcl(type_spec.get(key, str), value)
            return result

    if isinstance(type_spec, Path):
        return Path(value).resolve()


def to_tcl(value: Any) -> Any:
    """Based on https://github.com/Akuli/teek/blob/master/teek/_tcl_calls.py"""
    if isinstance(value, str):
        return value

    if value is None:
        return ""

    if isinstance(value, bool):
        return "1" if value else "0"

    if hasattr(value, "tcl_path"):
        return value.tcl_path

    if hasattr(value, "to_tcl"):
        return value.to_tcl()

    if isinstance(value, numbers.Real):
        return str(value)

    if isinstance(value, collections.abc.Mapping):
        return tuple(map(to_tcl, _flatten(value.items())))

    if callable(value):
        return create_command(value)

    if isinstance(value, Path):
        return str(value.resolve())

    return tuple(map(to_tcl, value))


class ClassPropertyDescriptor:
    # Source: https://stackoverflow.com/a/5191224
    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, owner: object | None = None):
        return self.fget.__get__(obj, owner or type(obj))()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        if isclass(obj):
            type_ = obj
            obj = None
        else:
            type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func: Callable | classmethod) -> ClassPropertyDescriptor:
        if not isinstance(func, classmethod):
            func = classmethod(func)
        self.fset = func
        return self


class ClassPropertyMetaClass(type):
    def __setattr__(self, key: str, value: Any):
        if key in self.__dict__:
            obj = self.__dict__.get(key)

            if obj and type(obj) is ClassPropertyDescriptor:
                return obj.__set__(self, value)

        return super(ClassPropertyMetaClass, self).__setattr__(key, value)


def classproperty(func: Callable | classmethod) -> ClassPropertyDescriptor:
    if not isinstance(func, classmethod):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)
