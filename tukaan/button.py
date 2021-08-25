from typing import Any, Callable, Dict, Tuple, Union

from ._base import BaseWidget, TkWidget


class Button(BaseWidget):
    _keys: Dict[str, Union[Any, Tuple[Any, str]]] = {
        "callback": (Callable, "command"),
        "style": str,
        "text": str,
    }

    def __init__(
        self,
        master: Union[TkWidget, None] = None,
        text: str = "",
        style: str = "TButton",
        callback: Union[Callable, None] = None,
    ) -> None:
        BaseWidget.__init__(
            self, master, "ttk::button", text=text, style=style, command=callback
        )

    def invoke(self):
        return self._tcl_call(None, self, "invoke")
