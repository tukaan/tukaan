import collections
import itertools
import numbers
from inspect import isclass
from typing import Any, Callable

counts: collections.defaultdict = collections.defaultdict(lambda: itertools.count(1))


class TukaanError(Exception):
    ...


def updated(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        get_tcl_interp().tcl_call(None, "update", "idletasks")
        result = func(self, *args, **kwargs)
        get_tcl_interp().tcl_call(None, "update", "idletasks")
        return result

    return wrapper


def update_before(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        get_tcl_interp().tcl_call(None, "update", "idletasks")
        return func(self, *args, **kwargs)

    return wrapper


def update_after(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        result = func(self, *args, **kwargs)
        get_tcl_interp().tcl_call(None, "update", "idletasks")
        return result

    return wrapper


def get_tcl_interp():
    from .app import App, tcl_interp

    if tcl_interp is None:
        try:
            tcl_interp = App()
        except Exception as e:
            raise TukaanError(e)

    return tcl_interp


_flatten = itertools.chain.from_iterable


def from_tcl(type_spec, value):
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
        stringed_value = from_tcl(str, value)
        if not stringed_value:
            return None
        return int(stringed_value, 0)

    if isinstance(type_spec, type):
        if issubclass(type_spec, numbers.Real):
            string = from_tcl(str, value)
            if not string:
                return None
            return type_spec(string)

        if hasattr(type_spec, "from_tcl"):
            string = from_tcl(str, value)

            if not string:
                return None

            return type_spec.from_tcl(string)

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
                type_spec = type_spec * len(items)
            return tuple(map(from_tcl, type_spec, items))

        if isinstance(type_spec, dict):
            # {'a': int, 'b': str} -> {'a': 1, 'b': 'hello', 'c': 'str assumed'}
            result = {}
            for key, value in _pairs(items):
                key = from_tcl(str, key)
                result[key] = from_tcl(type_spec.get(key, str), value)
            return result


def to_tcl(value):
    """Based on https://github.com/Akuli/teek/blob/master/teek/_tcl_calls.py"""

    if isinstance(value, str):
        return value

    if value is None:
        return None

    if isinstance(value, bool):
        return "1" if value else "0"

    if hasattr(value, "to_tcl"):
        return value.to_tcl()

    if isinstance(value, numbers.Real):
        return str(value)

    if isinstance(value, collections.abc.Mapping):
        return tuple(map(to_tcl, _flatten(value.items())))

    return tuple(map(to_tcl, value))


class ClassPropertyDescriptor:
    # Source: https://stackoverflow.com/a/5191224
    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, owner=None):
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

    def setter(self, func):
        if not isinstance(func, classmethod):
            func = classmethod(func)
        self.fset = func
        return self


class ClassPropertyMetaClass(type):
    def __setattr__(self, key, value):
        if key in self.__dict__:
            obj = self.__dict__.get(key)
        if obj and type(obj) is ClassPropertyDescriptor:
            return obj.__set__(self, value)

        return super(ClassPropertyMetaClass, self).__setattr__(key, value)


def classproperty(func):
    if not isinstance(func, classmethod):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)