import itertools

import pytest
from PIL import Image as PillowImage

from tukaan._base import Widget
from tukaan._images import (
    Image,
    ImageAnimator,
    convert_pillow_to_tk,
    create_animated_image,
    create_image,
    get_image_mode,
)
from tukaan._properties import OptionDescriptor
from tukaan._tcl import Tcl


def test_image_initialization(root, tests_dir):
    image = PillowImage.open(tests_dir / "spam.png")
    widget = Image(root, image)
    assert widget.parent is root
    assert widget.image is image


def test_image_prop_setter(root, tests_dir):
    widget = Image(root)
    image = PillowImage.open(tests_dir / "spam.png")
    assert widget.image is None

    widget.image = image
    assert widget.image == image

    widget.image = None
    assert widget.image is None


def test_get_image_mode():
    image1 = PillowImage.new("RGB", (100, 100))
    assert get_image_mode(image1) == "RGB"

    image2 = PillowImage.new("P", (100, 100))
    image2.putpalette([0, 0, 0, 255, 255, 255])
    assert get_image_mode(image2) == "RGB"


def test_create_image(tests_dir):
    image = PillowImage.open(tests_dir / "spam.png")
    name, _ = create_image(image)
    assert isinstance(name, str)
    assert name in Tcl.call([str], "image", "names")


def test_create_animated_image(tests_dir):
    image = PillowImage.open(tests_dir / "ham.gif")
    name = create_animated_image(image)
    assert isinstance(name, str)
    assert name in Tcl.call([str], "image", "names")


def test_convert_pillow_to_tk(tests_dir):
    image = PillowImage.open(tests_dir / "spam.png")
    name = convert_pillow_to_tk(image)
    assert isinstance(name, str)
    assert name in Tcl.call([str], "image", "names")


def test_convert_pillow_to_tk_animated(tests_dir, update):
    image = PillowImage.open(tests_dir / "ham.gif")
    name = convert_pillow_to_tk(image)
    assert isinstance(name, str)
    assert name in Tcl.call([str], "image", "names")
