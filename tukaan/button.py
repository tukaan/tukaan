from ._base import BaseWidget, TkWidget

from typing import Dict, Callable


class Button(BaseWidget):
    _keys: Dict[str, Any] = {"command": str}

    def __init__(self, master: Union[TkWidget, None]=None, text: str = "", style: str="TButton", command: Union[Callable, None]=None) -> None:
        BaseWidget.__init__(
            self,
            master,
            "ttk::button",
            text=text,
            style=style,
            command=command
        )
