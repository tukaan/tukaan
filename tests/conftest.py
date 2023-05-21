import pytest

import tukaan
from tukaan._tcl import Tcl


@pytest.fixture(autouse=True, scope="session")
def app():
    yield tukaan.App("Test App")


@pytest.fixture(scope="session")
def root():
    yield tukaan.MainWindow("Test window")


@pytest.fixture()
def update():
    yield lambda: Tcl.call(None, "update")
