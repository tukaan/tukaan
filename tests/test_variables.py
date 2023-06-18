from decimal import Decimal
from fractions import Fraction

import pytest

from tukaan import BoolVar, ControlVariable, FloatVar, IntVar, StringVar


def test_string_var():
    var = StringVar()
    assert var.value == ""
    var.value = "Hello"
    assert var.value == "Hello"


def test_int_var():
    var = IntVar()
    assert var.value == 0
    var.value = 0xABCDEF
    assert var.value == 0xABCDEF


def test_float_var():
    var = FloatVar()
    assert var.value == 0.0
    var.value = 3.141592653589793
    assert var.value == 3.141592653589793


def test_bool_var():
    var = BoolVar()
    assert var.value is False
    var.value = True
    assert var.value is True


def test_control_variable_default():
    TestVariable = type("TestVariable", (ControlVariable,), {"_default": "spam"})
    var = TestVariable()
    assert var._default == "spam"
    assert var.value == "spam"


def test_control_variable_with_init_value():
    TestVariable = type("TestVariable", (ControlVariable,), {"_default": 1234})
    var = TestVariable(9876)
    assert var._default == 1234
    assert var.value == 9876


def test_control_variable_get_class_for_type():
    _ = ControlVariable.get_class_for_type

    assert _("") is StringVar
    assert _(0) is IntVar
    assert _(0.0) is FloatVar
    assert _(Fraction(1, 2)) is FloatVar
    assert _(False) is BoolVar

    with pytest.raises(TypeError):
        _(Decimal("3.14"))

    with pytest.raises(TypeError):
        _(1j)
