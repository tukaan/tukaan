from __future__ import annotations

from typing import Callable

from tukaan._base import InputControl, TkWidget, WidgetBase
from tukaan._props import CommandProp, FocusableProp, LinkProp, TextProp, WidthProp, cget, config
from tukaan._tcl import Tcl
from tukaan._variables import ControlVariable, StringVar
from tukaan.enums import Orientation
from tukaan.widgets.frame import Frame


class RadioButton(WidgetBase, InputControl):
    _tcl_class = "ttk::radiobutton"

    action = CommandProp()
    focusable = FocusableProp()
    target = LinkProp()
    text = TextProp()
    width = WidthProp()

    def __init__(
        self,
        parent: TkWidget,
        text: str,
        value: float | str | bool,
        target: ControlVariable,
        *,
        focusable: bool | None = None,
        action: Callable[..., None] | None = None,
        tooltip: str | None = None,
        width: int | None = None,
    ) -> None:
        if not isinstance(value, target._type_spec):
            raise TypeError("value type must match the target control variable's type.")
        self._variable = target

        WidgetBase.__init__(
            self,
            parent,
            command=action,
            takefocus=focusable,
            text=text,
            tooltip=tooltip,
            value=value,
            variable=target,
            width=width,
        )

    def _repr_details(self) -> str:
        return f"value: {self.value}"

    def invoke(self) -> None:
        """Invoke the radiobutton, as if it were clicked."""
        Tcl.call(None, self, "invoke")

    def select(self) -> None:
        """Select the radiobutton."""
        self._variable.set(self.value)

    @property
    def selected(self) -> bool:
        """Return whether the radiobutton is selected or not."""
        return self._variable.get() == self.value

    @property
    def value(self) -> float | str | bool:
        return cget(self, self._variable._type_spec, "-value")

    @value.setter
    def value(self, value: float | str | bool) -> None:
        if not isinstance(value, self._variable._type_spec):
            raise TypeError("value type must match the target control variable's type.")

        config(self, value=value)


class RadioGroup(Frame, InputControl):
    _items: dict[str, RadioButton]

    def __init__(
        self,
        parent: TkWidget,
        items: dict[str, str],
        *,
        orientation: Orientation = Orientation.Vertical,
        padding: int | tuple[int, ...] | None = None,
        selected: str | None = None,
    ) -> None:
        super().__init__(parent, padding=padding)

        self._items = {}
        self._variable = StringVar(selected or tuple(items.keys())[0])
        self._orient = orientation
        self._setup_items(items)

    def _repr_details(self) -> str:
        item_id = self._variable.get()
        if item_id not in self._items:
            item_id = None

        return f"number of items={len(self._items)}, selected={item_id!r}"

    def _setup_items(self, items: dict[str, str]) -> None:
        for (value, text) in items.items():
            radio = RadioButton(self, text, value, self._variable)
            self._items[value] = radio

        self._regrid()

    def _regrid(self) -> None:
        is_vert = self._orient is Orientation.Vertical

        for index, radio in enumerate(self._items.values()):
            if is_vert:
                Tcl.call(None, "grid", radio, "-row", index, "-column", 0, "-sticky", "w")
            else:
                Tcl.call(None, "grid", radio, "-row", 0, "-column", index)

    def __getitem__(self, item: str) -> RadioButton | None:
        return self._items[item]

    def append(self, value: str, text: str) -> None:
        self._items[value] = RadioButton(self, text, value, self._variable)
        self._regrid()  # TODO: maybe not the best solution here

    def remove(self, item: str) -> None:
        radio = self._items.pop(item, None)

        if radio is not None:
            radio.destroy()
        else:
            raise ValueError(f"RadioGroup.remove({item!r}): {item!r} not in radio group")

    def select(self, item: str | None) -> None:
        if item in self._items:
            self._variable.set(item)
        elif item is None:
            self._variable.set("")
        else:
            raise ValueError(f"RadioGroup.select({item!r}): {item!r} not in radio group")

    @property
    def value(self) -> str:
        return self._variable.get() or None

    @value.setter
    def value(self, item: str | None) -> None:
        if item in self._items:
            self._variable.set(item)
        elif item is None:
            self._variable.set("")
        else:
            raise ValueError(f"RadioGroup.value = {item!r}: {item!r} not in radio group")

    @property
    def selected(self) -> RadioButton | None:
        return self._items.get(self._variable.get())

    @selected.setter
    def selected(self, item: RadioButton | None) -> None:
        if item in self._items.values():
            item.select()
        elif item is None:
            self._variable.set("")
        else:
            raise ValueError(f"RadioGroup.selected = {item!r}: {item!r} not in radio group")

    @property
    def orientation(self) -> Orientation:
        return self._orient

    @orientation.setter
    def orientation(self, value: Orientation) -> None:
        self._orient = value
        self._regrid()
