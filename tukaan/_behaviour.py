from __future__ import annotations


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
