from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import FunctionType

from tukaan._tcl import Procedure, Tcl


def test_convert_from_tcl_str(*_):
    for string in ("", "test_convert_str_from_tcl"):
        assert Tcl.call(str, "set", "test_var", string) == string


def test_convert_from_tcl_int():
    for number in (0, 3, 65536, 1234567890):
        result = Tcl.call(int, "set", "test_var", number)
        assert isinstance(result, int)
        assert result == number


def test_convert_from_tcl_float():
    for number in (0, 0.0, 0.1, 3.141592653):
        result = Tcl.call(float, "set", "test_var", number)
        assert isinstance(result, float)
        assert result == number


def test_Nonelike_to_number():
    for none in (False, ""):
        for type_ in (int, float):
            result = Tcl.call(type_, "set", "test_var", none)
            assert isinstance(result, type_)
            assert result == 0


def test_convert_from_tcl_bool():
    truthy = ["true", "tru", "yes", "y", "on", "1"]
    falsy = ["false", "fal", "no", "n", "off", "0"]

    for string in truthy:
        assert Tcl.call(bool, "set", "test_var", string.upper()) is True
        assert Tcl.call(bool, "set", "test_var", string.lower()) is True

    for string in falsy:
        assert Tcl.call(bool, "set", "test_var", string.upper()) is False
        assert Tcl.call(bool, "set", "test_var", string.lower()) is False

    for boolean in (0, 1, False, True):
        assert Tcl.call(bool, "set", "test_var", boolean) == boolean


def test_convert_from_tcl_set():
    assert Tcl.call({int}, "set", "test_var", Tcl.to({1, 2, 3})) == {1, 2, 3}


def test_convert_from_tcl_list():
    assert Tcl.call([int], "set", "test_var", Tcl.to([1, 2, 3])) == [1, 2, 3]


def test_convert_from_tcl_tuple():
    assert Tcl.call((int,), "set", "test_var", Tcl.to((1, 2, 3))) == (1, 2, 3)


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


def test_convert_from_tcl_callable():
    def spammer_function():
        pass

    tcl_proc_name = Tcl.to(spammer_function)
    assert tcl_proc_name in Tcl.call({str}, "info", "commands")

    result = Tcl.from_(Procedure, tcl_proc_name)
    assert isinstance(result, FunctionType)
    assert callable(result)
    assert result is spammer_function


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
