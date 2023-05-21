from tukaan import Button


def test_button_text_and_action(root):
    stuff = []
    command = lambda: stuff.append("foo")

    button1 = Button(root)
    button2 = Button(root, text="Text")
    button3 = Button(root, text="Text", action=command)

    assert button1.text == ""
    assert button2.text == "Text"
    assert button2.text == button3.text

    assert button2.action is None
    assert button3.action is command

    button2.action = button3.action
    assert button2.action is command

    result = button2.invoke()
    assert result is None
    assert "foo" in stuff

    result = button3.invoke()
    assert result is None
    assert stuff == ["foo", "foo"]


def test_button_properties(root, update):
    button = Button(root, width=10)
    button.grid()
    update()

    assert button.width == 10
    button.width = 2
    assert button.width == 2

    assert button.focusable
    button.focusable = False
    assert not button.focusable

    assert button.parent is root
