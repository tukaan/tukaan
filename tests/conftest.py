import pytest

import tukaan
from tukaan._tcl import Tcl


@pytest.fixture(autouse=True, scope="session")
def app():
    return tukaan.App("Test App")


@pytest.fixture(scope="session")
def root():
    return tukaan.MainWindow("Test window")


@pytest.fixture()
def update():
    return lambda: Tcl.call(None, "update")
