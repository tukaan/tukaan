import pytest

from tests.base import with_app_context
from tukaan import App, MainWindow
from tukaan.errors import AppAlreadyExistsError, MainWindowAlreadyExistsError


@with_app_context
def test_cant_create_multiple_app_contexts(app, window):
    with pytest.raises(AppAlreadyExistsError):
        App()


@with_app_context
def test_cant_create_multiple_main_windows(app, window):
    with pytest.raises(MainWindowAlreadyExistsError):
        MainWindow()
