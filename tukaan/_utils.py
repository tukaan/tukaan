from __future__ import annotations

import collections
import collections.abc
import itertools
from inspect import isclass
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Iterator

from ._info import System

if TYPE_CHECKING:
    from PIL import Image  # type: ignore

    from ._base import TkWidget
    from ._font import Font
    from ._images import Icon, _image_converter_class
    from ._variables import _TclVariable
    from .textbox import Tag
    from .timeout import Timeout


class count:
    """Simplified itertools.count"""

    def __init__(self, start: int = 0) -> None:
        self._count = start

    def __next__(self) -> int:
        self._count += 1
        return self._count

    def __iter__(self) -> Iterator[int]:
        # method to make mypy happy
        yield self._count

    def __int__(self) -> int:
        return self._count


counts: DefaultDict[Any, Iterator[int]] = collections.defaultdict(lambda: count())


_commands: dict[str, Callable] = {}
_images: dict[str, _image_converter_class | Icon] = {}
_pil_images: dict[str, Image] = {}
_timeouts: dict[str, Timeout] = {}
_variables: dict[str, _TclVariable] = {}
_text_tags: dict[str, Tag] = {}
_widgets: dict[str, TkWidget] = {}
_fonts: dict[str, Font] = {}


def windows_only(func):
    def wrapper(*args, **kwargs):
        if System.os == "Windows":
            return func(*args, **kwargs)

    return wrapper


def mac_only(func):
    def wrapper(*args, **kwargs):
        if System.os == "macOS":
            return func(*args, **kwargs)

    return wrapper


def linux_only(func):
    def wrapper(*args, **kwargs):
        if System.os == "Linux":
            return func(*args, **kwargs)

    return wrapper


flatten = itertools.chain.from_iterable


def reversed_dict(dictionary: dict) -> dict:
    return {value: key for key, value in dictionary.items()}


def seq_pairs(sequence):
    return zip(sequence[0::2], sequence[1::2])


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
