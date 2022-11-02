from __future__ import annotations

import functools
import itertools
import sys
from typing import Any, Iterator, Sequence, TypeVar

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


class count:
    """Simplified itertools.count, that can be int()-ed."""

    def __init__(self, start: int = 0) -> None:
        self._count = start

    def __next__(self) -> int:
        self._count += 1
        return self._count

    def __iter__(self) -> Iterator[int]:
        yield self._count

    def __int__(self) -> int:
        return self._count


flatten = itertools.chain.from_iterable


def reversed_dict(dictionary: dict[object, object]) -> dict[object, object]:
    return {value: key for key, value in dictionary.items()}


def seq_pairs(sequence: Sequence[object]) -> Iterator[object]:
    return zip(sequence[::2], sequence[1::2])


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
