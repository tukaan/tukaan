from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from tests.base import with_app_context
from tukaan._tcl import Tcl


@with_app_context  # just to make sure the interpreter is initialized
def test_convert_from_tcl_str(app, window):
    result = Tcl.call(str, "set", "test_var", "test_convert_str_from_tcl")
    assert isinstance(result, str)
    assert result == "test_convert_str_from_tcl"


def test_convert_from_tcl_int():
    result = Tcl.call(int, "set", "test_var", "65536")
    assert isinstance(result, int)
    assert result == 65536


def test_convert_from_tcl_float():
    result = Tcl.call(float, "set", "test_var", "3.141591653")
    assert isinstance(result, float)
    assert result == 3.141591653


def test_convert_from_tcl_bool():
    result = Tcl.call(bool, "set", "test_var", "1")
    assert isinstance(result, bool)
    assert result is True

    result = Tcl.call(bool, "set", "test_var", "0")
    assert isinstance(result, bool)
    assert result is False

    result = Tcl.call(bool, "set", "test_var", "yes")
    assert isinstance(result, bool)
    assert result is True


def test_convert_from_tcl_set():
    result = Tcl.call({int}, "set", "test_var", Tcl.to({1, 2, 3}))
    assert isinstance(result, set)
    assert result == {1, 2, 3}


def test_convert_from_tcl_list():
    result = Tcl.call([int], "set", "test_var", Tcl.to([1, 2, 3]))
    assert isinstance(result, list)
    assert result == [1, 2, 3]


def test_convert_from_tcl_tuple():
    result = Tcl.call((int,), "set", "test_var", Tcl.to((1, 2, 3)))
    assert isinstance(result, tuple)
    assert result == (1, 2, 3)


def test_convert_from_tcl_dict():
    return_type = {"first": int, "second": float, "third": bool}
    result = Tcl.call(
        return_type, "set", "test_var", Tcl.to({"first": 1, "second": 1.23, "third": False})
    )
    assert isinstance(result, dict)
    for key, value in result.items():
        assert key in return_type
        assert isinstance(value, return_type[key])


def test_convert_from_tcl_pathlib_path():
    result = Tcl.call(Path, "set", "test_var", Tcl.to(Path("./foo.png")))
    assert isinstance(result, Path)
    assert result.name == "foo.png"
    assert result == Path.cwd() / "foo.png"


class Foo(Enum):
    Spam = "spam"
    Ham = "ham"
    Egg = "egg"


def test_convert_from_tcl_enum():
    result = Tcl.call(Foo, "set", "test_var", "ham")
    assert isinstance(result, Enum)
    assert result in Foo
    assert result is Foo.Ham

    result = Tcl.call(Foo, "set", "test_var", Tcl.to(Foo.Spam))
    assert isinstance(result, Enum)
    assert result in Foo
    assert result is Foo.Spam


@dataclass
class ClassWithFromTcl:
    value: str

    @classmethod
    def __from_tcl__(cls, string):
        return ClassWithFromTcl(value=string)


def test_convert_from_tcl_custom_object():
    result = Tcl.call(ClassWithFromTcl, "set", "test_var", "foo")
    assert isinstance(result, ClassWithFromTcl)
    assert result.value == "foo"


def test_convert_to_tcl_dict():
    result = Tcl.to({})
    assert isinstance(result, tuple)
    assert result == ()

    result = Tcl.to({"a": 1})
    assert isinstance(result, tuple)
    assert result == ("a", 1)

    result = Tcl.to({"a": {"a": {"a": 1}}})
    assert isinstance(result, tuple)
    assert result == ("a", ("a", ("a", 1)))
