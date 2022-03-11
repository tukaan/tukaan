from typing import Callable

from ._utils import delete_command, get_tcl_interp


class TimeOut:
    def __init__(self, time: float, func: Callable) -> None:
        self._func = func
        self._id = get_tcl_interp()._tcl_call(str, "after", int(time * 1000), self._call_func)
        self.state = "pending"

    def __repr__(self) -> str:
        return f"<{self.state.capitalize()} `{self._func.__name__}()` timeout>"

    def _call_func(self) -> None:
        try:
            self._func()
        except Exception:
            self.state = "failed"
        else:
            self.state = "succesfully completed"

    def cancel(self) -> None:
        if self.state != "pending":
            raise RuntimeError(f"cannot cancel a {self.state} timeout")

        after_id = get_tcl_interp()._tcl_call((str,), "after", "info", self._id)[0]
        get_tcl_interp()._tcl_call(None, "after", "cancel", after_id)
        delete_command(after_id)

        self.state = "cancelled"


class Timer:
    @staticmethod
    def wait(time: float) -> None:
        code = f"""
        set tukaan_waitvar 0
        after {time * 1000} {{set tukaan_waitvar 1}}
        tkwait variable tukaan_waitvar"""
        get_tcl_interp()._tcl_eval(None, code)

    @staticmethod
    def schedule(time: float, func: Callable) -> TimeOut:
        return TimeOut(time, func)

    @staticmethod
    def cancel(timeout: TimeOut) -> None:
        timeout.cancel()
