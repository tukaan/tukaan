from __future__ import annotations

import functools
import itertools
from typing import Any, Callable, Generic, Iterator, Sequence, TypeVar

from tukaan._typing import P, T

KT = TypeVar("KT")
VT = TypeVar("VT")


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


def reversed_dict(dictionary: dict[KT, VT]) -> dict[VT, KT]:
    return {value: key for key, value in dictionary.items()}


def seq_pairs(sequence: Sequence[T]) -> zip[tuple[T, T]]:
    return zip(sequence[::2], sequence[1::2])


class instanceclassmethod(Generic[T]):
    def __init__(self, method: Callable[P, T]) -> None:
        self.method = method

    def __get__(self, obj: Any, objtype: type):
        @functools.wraps(self.method)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if obj is None:
                return self.method(objtype, *args, **kwargs)
            return self.method(obj, *args, **kwargs)

        return wrapper


class classproperty(Generic[T]):
    def __init__(self, fget: Callable[P, T]):
        if not isinstance(fget, classmethod):
            fget = classmethod(fget)
        self.fget = fget

    def __get__(self, obj: Any, objtype: type):
        return self.fget.__get__(obj, objtype)()
