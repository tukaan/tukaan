from tukaan import BoolVar, CheckBox


def test_button_initialization(root):
    stuff = []
    command = lambda value: stuff.append(value)

    button1 = CheckBox(root)
    button2 = CheckBox(root, "Spam ham egg")
    button3 = CheckBox(root, "Spam ham egg", selected=True, action=command)

    assert button1.text == ""
    assert button2.text == "Spam ham egg"
    assert button2.text == button3.text

    assert not button1.selected
    assert not button2.selected
    assert button3.selected

    assert button2.action is None
    assert button3.action is command

    button2.action = button3.action
    assert button2.action is command

    button2.invoke()
    assert stuff and stuff[0] is True

    button3.invoke()
    assert stuff == [True, False]


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
