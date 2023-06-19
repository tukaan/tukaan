from tukaan import BoolVar, CheckBox


def test_checkbox_initialization(root):
    stuff = []
    callback = lambda value: stuff.append(value)

    checkbox1 = CheckBox(root)
    checkbox2 = CheckBox(root, "Spam ham egg")
    checkbox3 = CheckBox(root, "Spam ham egg", selected=True, action=callback)

    assert checkbox1.parent is root

    assert isinstance(checkbox1._variable, BoolVar)

    assert checkbox1.text == ""
    assert checkbox2.text == "Spam ham egg"
    assert checkbox2.text == checkbox3.text

    assert not checkbox1.selected
    assert not checkbox2.selected
    assert checkbox3.selected

    assert checkbox2.action is None
    assert checkbox3.action is callback

    checkbox2.action = checkbox3.action
    assert checkbox2.action is callback

    checkbox2.invoke()
    assert stuff and stuff[0] is True

    checkbox3.invoke()
    assert stuff == [True, False]


def test_checkbox_custom_link_var(root):
    link = BoolVar(True)
    checkbox = CheckBox(root, link=link)
    assert checkbox.selected
    assert checkbox._variable == link
    assert checkbox.link == link
    checkbox.link = None  # Should this be allowed?
    assert checkbox.link is None


### Methods


def test_checkbox_de_select(root):
    checkbox1 = CheckBox(root)
    checkbox1.select()
    assert checkbox1.selected

    checkbox2 = CheckBox(root, selected=True)
    checkbox2.deselect()
    assert not checkbox2.selected


def test_checkbox_toggle(root):
    checkbox = CheckBox(root, selected=True)
    checkbox.toggle()
    assert not checkbox.selected

    checkbox.toggle()
    assert checkbox.selected


### Properties


def test_checkbox_action_porperty(root):
    action_called = False

    def action(value):
        nonlocal action_called
        action_called = True

    checkbox = CheckBox(root)
    checkbox.action = action
    assert checkbox.action is action

    checkbox.invoke()
    assert action_called


def test_checkbox_selected_property(root):
    checkbox = CheckBox(root)
    checkbox.selected = True
    assert checkbox.selected

    checkbox.selected = False
    assert not checkbox.selected


def test_checkbox_width_property(root):
    checkbox = CheckBox(root, width=10)
    checkbox.grid()

    assert checkbox.width == 10
    checkbox.width = 2
    assert checkbox.width == 2
