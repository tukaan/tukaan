from PIL import Image
from tukaan import Label
from tukaan.enums import Anchor, Justify, ImagePosition


def test_label_initialization(root):
    label1 = Label(root)
    label2 = Label(root, "Spam & egg")
    label3 = Label(root, "Spam & egg", align=Anchor.Left, justify=Justify.Center)
    image = Image.new("RGB", (100, 100))
    label4 = Label(root, image=image, image_pos=ImagePosition.Right, max_line_length=123)

    assert label1.parent is root

    assert label1.text == ""
    assert label2.text == "Spam & egg"
    assert label2.text == label3.text

    assert label1.align is Anchor.Center
    assert label2.justify is Justify.Left

    assert label4.image == image
    assert label4.image_pos is ImagePosition.Right
    assert label4.max_line_length == 123


def test_label_image_property(root, tests_dir):
    img = Image.open(tests_dir / "spam.png")
    label = Label(root, image=img)
    assert label.image == img

    label.image = None
    assert label.image is None


def test_label_image_pos_property(root):
    label = Label(root)
    assert label.image_pos is ImagePosition.Above

    for position in ImagePosition:
        label.image_pos = position
        assert label.image_pos is position

    label.image_pos = None
    assert label.image_pos is ImagePosition.Default


def test_label_align_property(root):
    label = Label(root)
    assert label.align is Anchor.Center

    for position in Anchor:
        label.align = position
        assert label.align is position


def test_label_justify_property(root):
    label = Label(root)
    assert label.justify is Justify.Left

    for position in Justify:
        label.justify = position
        assert label.justify is position


def test_label_max_line_length_property(root):
    label = Label(root)
    assert label.max_line_length == 0

    label.max_line_length = 80
    assert label.max_line_length == 80
