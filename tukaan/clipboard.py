from __future__ import annotations

from tukaan._tcl import Tcl
from tukaan.exceptions import TukaanTclError


class Clipboard:
    def __repr__(self) -> str:
        return f"<tukaan.Clipboard; content: {self.paste()}>"

    @classmethod
    def clear(cls) -> None:
        Tcl.call(None, "clipboard", "clear")

    @classmethod
    def append(cls, content: str) -> None:
        Tcl.call(None, "clipboard", "append", content)

    @classmethod
    def paste(cls) -> str:
        try:
            return Tcl.call(str, "clipboard", "get")
        except TukaanTclError:
            return ""

    @classmethod
    def copy(cls, content: str) -> None:
        Tcl.call(None, "clipboard", "clear")
        Tcl.call(None, "clipboard", "append", content)
