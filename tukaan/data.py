from __future__ import annotations


class TabStop:
    def __init__(self, position: float, align: str = "left"):
        if align == "decimal":
            align = "numeric"

        self.position, self.align = position, align

    def __repr__(self):
        return f"TabStop({self.position!r}, {self.align!r})"

    def __to_tcl__(self):
        return self.position, self.align
