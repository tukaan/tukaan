from typing import Any, Callable


class Event:
    data: Any
    sequence: str
    callback: Callable

    def __init__(self, sequence: str, func: Callable, data: Any) -> None:
        self.sequence = sequence
        self.callback = func
        self.data = data

    def __repr__(self) -> str:
        ignored_values = {None, "??", -1, 0}
        relevant_attrs = ("delta", "sequence", "keysymbol")
        pairs = []

        for name in relevant_attrs:
            value = getattr(self, name)
            if value not in ignored_values:
                pairs.append(f"{name}={value!r}")
        if self.data is not None:
            pairs.append(f"data={self.data!r}")
        pairs.append(f"callback=`{self.callback.__name__}()`")

        return f"<Event: {', '.join(sorted(pairs))}>"
