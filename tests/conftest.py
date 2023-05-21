import pytest

import tukaan
from tukaan._tcl import Tcl

app_object = tukaan.App("Test App")
window_object = tukaan.MainWindow("Test window")


def update_func():
    Tcl.call(None, "update")


@pytest.fixture
def update():
    yield update_func


@pytest.fixture
def app():
    yield app_object


@pytest.fixture
def root():
    yield window_object
