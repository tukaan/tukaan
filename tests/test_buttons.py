from PIL import Image

from tukaan import Button


def test_button_initialization(root):
    stuff = []
    callback = lambda: stuff.append("foo")

    button1 = Button(root)
    button2 = Button(root, "Spam ham egg")
    button3 = Button(root, "Spam ham egg", action=callback)

    assert button1.parent is root

    assert button1.text == ""
    assert button2.text == "Spam ham egg"
    assert button2.text == button3.text

    assert button2.action is None
    assert button3.action is callback

    button2.action = button3.action
    assert button2.action is callback

    button2.invoke()
    assert "foo" in stuff

    button3.invoke()
    assert stuff == ["foo", "foo"]


### Properties


def test_button_image_property(root, tests_dir):
    img = Image.open(tests_dir / "spam.png")
    button = Button(root, image=img)
    button.grid()

    assert button.image == img
    button.image = None
    assert button.image is None


def test_button_width_property(root):
    button = Button(root, width=10)
    button.grid()

    assert button.width == 10
    button.width = 2
    assert button.width == 2
