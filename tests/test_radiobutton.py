import pytest

from tukaan import BoolVar, ControlVariable, FloatVar, IntVar, RadioButton, StringVar


def test_radiobutton_initialization(root):
    stuff = []
    callback = lambda: stuff.append("foo")

    radio1 = RadioButton(root, "", "spam", StringVar())
    radio2 = RadioButton(root, "Spam ham egg")
    radio3 = RadioButton(root, "Spam ham egg", action=callback)

    assert radio1.parent is root
    assert radio2.parent is root
    assert radio3.parent is root

    assert isinstance(radio1._variable, StringVar)
    assert isinstance(radio2._variable, IntVar)
    assert isinstance(radio3._variable, IntVar)

    assert radio1.text == ""
    assert radio2.text == "Spam ham egg"
    assert radio3.text == radio2.text

    assert radio2.action is None
    assert radio3.action is callback

    radio2.action = radio3.action
    assert radio2.action is callback

    radio2.invoke()
    assert "foo" in stuff

    radio3.invoke()
    assert stuff == ["foo", "foo"]


def test_radiobutton_init_value_guess_link_type(root):
    radio1 = RadioButton(root, value="foo")
    assert isinstance(radio1._variable, StringVar)

    radio2 = RadioButton(root, value=1)
    assert isinstance(radio2._variable, IntVar)

    radio3 = RadioButton(root, value=1.0)
    assert isinstance(radio3._variable, FloatVar)

    radio4 = RadioButton(root, value=True)
    assert isinstance(radio4._variable, BoolVar)

    with pytest.raises(TypeError):
        RadioButton(root, value=1j)


def test_radiobutton_init_value_type_mismatch(root):
    with pytest.raises(TypeError):
        RadioButton(root, value=1, link=BoolVar())

    with pytest.raises(TypeError):
        RadioButton(root, value=1, link=FloatVar())

    with pytest.raises(TypeError):
        RadioButton(root, value=1.0, link=IntVar())


def test_radiobutton_selected(root):
    link1 = StringVar("default value")
    radio1 = RadioButton(root, value="foo", link=link1)

    assert not radio1.selected

    radio1.select()

    assert radio1.selected

    link2 = StringVar("default value")
    radio2 = RadioButton(root, value="default value", link=link2)

    assert radio2.selected


def test_radiobutton_value(root):
    radio = RadioButton(root, value="spam")
    assert radio.value == "spam"

    radio.value = "ham"
    assert radio.value == "ham"


def test_radiobutton_value_type_mismatch(root):
    radio = RadioButton(root, "Some stuff", True)

    with pytest.raises(TypeError):
        radio.value = "string value"


def test_radiobutton_link_with_another(root):
    radio1 = RadioButton(root, "Radio 1")
    radio2 = RadioButton(root, "Radio 2", link=radio1)

    assert radio1.link is radio2.link

    radio3 = RadioButton(root, "Radio 3")

    radio3.link = radio1
    assert radio1.link is radio3.link

    with pytest.raises(TypeError):
        RadioButton(root, "Radio 3", "invalid value", link=radio3)
