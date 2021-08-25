from typing import Any, Callable, Dict, Tuple, Union

from ._base import BaseWidget, TkWidget


class Button(BaseWidget):
    _keys: Dict[str, Union[Any, Tuple[Any, str]]] = {
        "callback": (Callable, "command"),
        "style": str,
        "text": str,
        "underline": int,
        "width": int,
    }

    def __init__(
        self,
        master: Union[TkWidget, None] = None,
        callback: Union[Callable, None] = None,
        style: str = "TButton",
        text: str = "",
        underline: int = None,
        width: int = None,
    ) -> None:
        BaseWidget.__init__(
            self,
            master,
            "ttk::button",
            command=callback,
            style=style,
            text=text,
            width=width,
            underline=underline,
        )

    def invoke(self):
        return self._tcl_call(None, self, "invoke")
