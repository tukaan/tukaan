from typing import Any, Callable, Optional

from ._tcl import Tcl


class Timeout:
    _id: Optional[str] = None
    _repeat: bool = False
    state: str = "not started"

    def __init__(self, seconds: float, target: Callable[[], Any], *, args=(), kwargs={}) -> None:
        self.seconds = seconds
        self.target = target

    def __repr__(self) -> str:
        return f"<{self.state.capitalize()} `{self.target.__name__}()` timeout>"

    def __call__(self) -> None:
        try:
            self.target()
        except Exception as e:
            print(e)
            self.state = "failed"
        else:
            self.state = "succesfully completed"

        if self._repeat:
            self.start()

    def start(self) -> None:
        self._id = Tcl.call(str, "after", int(self.seconds * 1000), self.__call__)
        self.state = "pending"

    def repeat(self) -> None:
        self._repeat = True
        self.start()

    def cancel(self) -> None:
        if self.state != "pending":
            raise RuntimeError(f"cannot cancel a {self.state} timeout")

        after_id, _ = Tcl.call((str,), "after", "info", self._id)
        Tcl.call(None, "after", "cancel", after_id)
        Tcl.delete_cmd(after_id)

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
        Tcl.call(
            str, "after", int(seconds * 1000), Tcl.create_cmd(target, args=args, kwargs=kwargs)
        )

    @staticmethod
    def wait(seconds: float) -> None:
        script = f"""
        set tukaan_waitvar 0
        after {int(seconds * 1000)} {{set tukaan_waitvar 1}}
        tkwait variable tukaan_waitvar"""
        Tcl.eval(None, script)

    @staticmethod
    def delay(seconds: float) -> Callable:
        def real_decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> Any:
                Timer.wait(seconds)
                return func(*args, **kwargs)

            return wrapper

        return real_decorator
