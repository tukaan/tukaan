import pytest

from tukaan import App, MainWindow
from tukaan.errors import AppAlreadyExistsError, MainWindowAlreadyExistsError


def test_cant_create_multiple_app_contexts():
    with pytest.raises(AppAlreadyExistsError):
        App()


def test_cant_create_multiple_main_windows():
    with pytest.raises(MainWindowAlreadyExistsError):
        MainWindow()
