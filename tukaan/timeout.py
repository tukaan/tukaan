from typing import Callable

from ._utils import _timeouts, counts, create_command, delete_command, get_tcl_interp


class Timeout:
    def __init__(self, time: float, func: Callable) -> None:
        self._name = f"tukaan_timeout_{next(counts['timeout'])}"

        self._func = func
        self._callback = create_command(self._call_func)

        self.id = get_tcl_interp()._tcl_call(
            str, "after", int(time * 1000), self._callback
        )

        _timeouts[self._name] = self

        self.state = "pending"

    def __repr__(self) -> str:
        return f"<{self.state} {self._callback} timeout>"

    def _call_func(self) -> None:
        # in terms of performance this is a bad idea, but i need that fancy "state"
        self._func()
        self.state = "succesfully completed"
        del _timeouts[self._name]

    def cancel(self) -> None:
        if self.state != "pending":
            raise RuntimeError(f"cannot cancel a {self.state} timeout")

        after_id = get_tcl_interp()._tcl_call([str], "after", "info", self.id)[0]
        get_tcl_interp()._tcl_call(None, "after", "cancel", after_id)

        delete_command(after_id)

        self.state = "cancelled"
        del _timeouts[self._name]
