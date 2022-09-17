from __future__ import annotations

import collections
import functools
import itertools
import sys
from typing import Any, Iterator, Sequence, TypeVar


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


flatten = itertools.chain.from_iterable


def reversed_dict(dictionary: dict[object, object]) -> dict[object, object]:
    return {value: key for key, value in dictionary.items()}


def seq_pairs(sequence: Sequence[object]) -> Iterator[object]:
    return zip(sequence[::2], sequence[1::2])


def windows_only(func) -> Any:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if sys.platform == "win32":
            return func(*args, **kwargs)

    return wrapper


def mac_only(func) -> Any:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if sys.platform == "aqua":
            return func(*args, **kwargs)

    return wrapper


def linux_only(func) -> Any:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if sys.platform == "linux":
            return func(*args, **kwargs)

    return wrapper


class instanceclassmethod:
    def __init__(self, method) -> None:
        self.method = method

    def __get__(self, obj: object | None, objtype: type):
        def wrapper(*args, **kwargs):
            if obj is None:
                return self.method(objtype, *args, **kwargs)
            return self.method(obj, *args, **kwargs)

        return wrapper


class classproperty:
    def __init__(self, fget):
        if not isinstance(fget, classmethod):
            fget = classmethod(fget)
        self.fget = fget

    def __get__(self, obj: object | None, objtype: type):
        return self.fget.__get__(obj, objtype)()
