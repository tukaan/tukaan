from typing import Callable


class TkWidget:
    destroy: Callable
    """Base class for every Tukaan widget"""

    @classmethod
    def _py_to_tcl_arguments(self, kwargs):
        result = []

        for key, value in kwargs.items():
            if value is None:
                continue

            if key.endswith("_"):
                key = key[:-1]

            if callable(value):
                continue  # TODO: create commands

            result.extend([f"-{key}", value])

        return tuple(result)
