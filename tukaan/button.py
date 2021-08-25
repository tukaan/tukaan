from typing import Any, Callable, Dict, Union

from ._base import BaseWidget, TkWidget


class Button(BaseWidget):
    # FIXME: return the actual function for command attribute, not the tcl name
    _keys: Dict[str, Any] = {"command": str, "style":str, "text": str}

    def __init__(
        self,
        master: Union[TkWidget, None] = None,
        text: str = "",
        style: str = "TButton",
        command: Union[Callable, None] = None,
    ) -> None:
        BaseWidget.__init__(
            self, master, "ttk::button", text=text, style=style, command=command
        )

    def invoke(self):
        return self._tcl_call(None, self, "invoke")
