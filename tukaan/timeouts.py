import functools
from typing import Any, Callable

from ._tcl import Tcl, TclCallback


class Timeout:
    _after_id: str = ""
    _repeat: bool = False
    state: str = "not started"

    def __init__(self, seconds: float, target: Callable[[], Any], *, args=(), kwargs={}) -> None:
        assert callable(target), "target must be callable"

        self.seconds = seconds
        self.target = target

    def __repr__(self) -> str:
        name = self.target.__name__
        if name != "<lambda>":
            name += "()"

        return f"<{self.state.capitalize()} `{name}` timeout at {hex(id(self))}>"

    def run_once(self):
        try:
            self.target()
        except Exception as e:
            print(e)
            self.state = "failed"

    def run_now(self):
        self.cancel()
        self.run_once()

    def run(self):
        try:
            self.target()
            if self._repeat:
                return self.start()
        except Exception as e:
            print(e)
            self.state = "failed"
        else:
            self.state = "succesfully completed"

    __call__ = run

    def start(self) -> None:
        self._after_id = Tcl.call(str, "after", int(self.seconds * 1000), self.__call__)
        self.state = "pending"

    def repeat(self) -> None:
        self._repeat = True
        self.start()

    def cancel(self) -> None:
        if self.state != "pending":
            raise RuntimeError(f"cannot cancel a {self.state} timeout")

        command, _ = Tcl.call((str,), "after", "info", self._after_id)
        Tcl.call(None, "after", "cancel", command)
        Tcl.delete_cmd(command)

        self._repeat = False
        self.state = "cancelled"

    @property
    def is_repeated(self) -> bool:
        return self._repeat

    @is_repeated.setter
    def is_repeated(self, repeat: bool) -> None:
        self._repeat = repeat


class Timer:
    @staticmethod
    def schedule(seconds: float, target: Callable[[Any], Any], *, args=(), kwargs={}) -> None:
        Tcl.call(str, "after", int(seconds * 1000), TclCallback(target, args=args, kwargs=kwargs))

    @staticmethod
    def wait(seconds: float) -> None:
        script = f"""
        set tukaan_waitvar 0
        after {int(seconds * 1000)} {{set tukaan_waitvar 1}}
        tkwait variable tukaan_waitvar"""

        Tcl.eval(None, script)

    @staticmethod
    def delayed(seconds: float) -> Callable:
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                Timer.wait(seconds)
                return func(*args, **kwargs)

            return wrapper

        return decorator
