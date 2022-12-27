from __future__ import annotations

from dataclasses import dataclass

class DashPattern:
    def __init__(self, pattern: list[int] | tuple[int, ...]) -> None:
        self._pattern = pattern

    @staticmethod
    def from_string(str_pattern: str) -> DashPattern:
        pattern_list = []

        for char in str_pattern:
            list_length_is_odd = len(pattern_list) % 2

            if char in ".,-_":
                value = ".,-_".index(char) + 1
                if list_length_is_odd:
                    pattern_list[-1] += value
                else:
                    pattern_list.append(value)
            elif char == " ":
                if not list_length_is_odd:
                    try:
                        pattern_list[-1] += 1
                    except IndexError:
                        raise ValueError("pattern can't start with empty space")
                else:
                    pattern_list.append(1)
            else:
                raise ValueError(f"invalid character in pattern: {char!r}")

        if len(pattern_list) % 2:
            # Pattern must end with an empty space
            pattern_list.append(1)

        return DashPattern(pattern_list)

    def __to_tcl__(self):
        return tuple(str(x) for x in self._pattern)

    @staticmethod
    def __from_tcl__(value):
        ...

@dataclass
class ArrowHead:
    length: float = None
    width: float = None
    fill: float = None

    def _get_startarrow(self):
        return dict(
            startarrow=True,
            startarrowlength=self.length,
            startarrowwidth=abs(self.width),
            startarrowfill=self.fill,
        )

    def _get_endarrow(self):
        return dict(
            endarrow=True,
            endarrowlength=self.length,
            endarrowwidth=abs(self.width),
            endarrowfill=self.fill,
        )

    def __to_tcl__(self) -> tuple:
        return self._get_endarrow()

    @classmethod
    def __from_tcl__(cls, value):
        ...
