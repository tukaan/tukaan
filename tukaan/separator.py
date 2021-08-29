from typing import Literal, Union, Dict, Any, Tuple
from ._base import BaseWidget, TukaanWidget


class Separator(BaseWidget):
    _keys: Dict[str, Union[Any, Tuple[Any, str]]] = {"orientation": (str, "orient")}

    def __init__(
        self,
        parent: Union[TukaanWidget, None] = None,
        orientation: Union[Literal["horizontal", "vertical"], None] = None,
    ) -> None:
        BaseWidget.__init__(self, parent, "ttk::separator", orient=orientation)

    def _repr_details(self):
        return f"orientation={self.orientation!r}"
