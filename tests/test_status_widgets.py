import pytest

from tukaan import ProgressBar
from tukaan.enums import Orientation, ProgressMode
from tukaan._tcl import Tcl


def test_progressbar_properties(root):
    progress_bar = ProgressBar(
        root, max=160, length=300, mode=ProgressMode.Determinate, orientation=Orientation.Vertical
    )

    assert progress_bar.max == 160
    assert progress_bar.length == 300
    assert progress_bar.mode is ProgressMode.Determinate
    assert progress_bar.orientation is Orientation.Vertical

    progress_bar.max = 50
    progress_bar.length = 123
    progress_bar.mode = ProgressMode.Indeterminate
    progress_bar.orientation = Orientation.Vertical

    assert progress_bar.max == 50
    assert progress_bar.length == 123
    assert progress_bar.mode is ProgressMode.Indeterminate
    assert progress_bar.orientation is Orientation.Vertical


def test_progress_bar_step(root):
    progress_bar = ProgressBar(root)

    progress_bar.step(10)
    assert progress_bar.value == 10


def test_progress_bar_start_and_stop(root):
    progress_bar = ProgressBar(root)

    progress_bar.start(1000)
    progress_bar.stop()


def test_progress_bar_step_through(root):
    progress_bar = ProgressBar(root)

    stepper = progress_bar.step_through()
    assert next(stepper) == 0

    for i in range(1, progress_bar.max):
        assert next(stepper) == i
