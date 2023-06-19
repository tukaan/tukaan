import pytest
from PIL import Image

from tukaan import Divider
from tukaan.enums import Orientation


def test_button_initialization(root):
    divider1 = Divider(root)
    divider2 = Divider(root, Orientation.Vertical)

    assert divider1.parent is root
    assert divider2.parent is root

    assert divider1.orientation is Orientation.Horizontal
    assert divider2.orientation is Orientation.Vertical


### Properties


def test_divider_orientation_property(root):
    divider = Divider(root)

    assert divider.orientation is Orientation.Horizontal
    divider.orientation = Orientation.Vertical
    assert divider.orientation is Orientation.Vertical
    with pytest.raises(TypeError):
        divider.orientation = None
