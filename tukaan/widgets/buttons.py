from __future__ import annotations

from typing import Callable

from PIL.Image import Image

from tukaan._base import TkWidget, Widget
from tukaan._images import ImageProp
from tukaan._properties import ActionProp, FocusableProp, IntDesc, LinkProp, StrDesc, cget, config
from tukaan._tcl import Tcl
from tukaan._variables import BoolVar, ControlVariable, IntVar


class Button(Widget, widget_cmd="ttk::button", tk_class="TButton"):
    action = ActionProp()
    focusable = FocusableProp()
    text = StrDesc()
    width = IntDesc()
    image = ImageProp()

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        action: Callable | None = None,
        *,
        focusable: bool | None = None,
        image: Image | None = None,
        width: int | None = None,
    ) -> None:
        super().__init__(
            parent, command=action, image=image, takefocus=focusable, text=text, width=width
        )

    def invoke(self) -> None:
        """Invoke this button, as if it had been clicked."""
        Tcl.call(None, self, "invoke")


class CheckBox(Widget, widget_cmd="ttk::checkbutton", tk_class="TCheckbutton"):
    _variable: BoolVar

    focusable = FocusableProp()
    link = LinkProp[bool]()
    text = StrDesc()
    width = IntDesc()

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        *,
        action: Callable[[bool], None] | None = None,
        focusable: bool | None = None,
        link: BoolVar | None = None,
        selected: bool = False,
        width: int | None = None,
    ) -> None:
        self._variable = BoolVar(selected) if link is None else link
        self._action = action

        super().__init__(
            parent,
            command=self._call_action,
            offvalue=False,
            onvalue=True,
            takefocus=focusable,
            text=text,
            variable=self._variable,
            width=width,
        )

    def _call_action(self) -> None:
        if self._action is not None:
            self._action(self._variable.get())

    def invoke(self) -> None:
        """Invoke this checkbox, as if it had been clicked."""
        Tcl.call(None, self, "invoke")

    def select(self) -> None:
        """Select this checkbox."""
        self._variable.set(True)

    def deselect(self) -> None:
        """Deselect this checkbox."""
        self._variable.set(False)

    def toggle(self) -> None:
        """Toggle the state of this checkbox."""
        self._variable.set(not self._variable.get())

    @property
    def selected(self) -> bool:
        """Get or set whether this checkbox is currently selected."""
        return self._variable.get()

    @selected.setter
    def selected(self, value: bool) -> None:
        self._variable.set(value)

    @property
    def action(self) -> Callable[[bool], None] | None:
        return self._action

    @action.setter
    def action(self, func: Callable[[bool], None] | None) -> None:
        self._action = func


class RadioButton(Widget, widget_cmd="ttk::radiobutton", tk_class="TRadiobutton"):
    action = ActionProp()
    focusable = FocusableProp()
    link = LinkProp[object]()
    text = StrDesc()
    width = IntDesc()

    def __init__(
        self,
        parent: TkWidget,
        text: str | None = None,
        value: float | str | bool = 0,
        link: ControlVariable | TkWidget | None = None,
        *,
        action: Callable[..., None] | None = None,
        focusable: bool | None = None,
        width: int | None = None,
    ) -> None:
        if isinstance(link, ControlVariable):
            self._variable = link
        elif isinstance(link, RadioButton):
            self._variable = link._variable
        elif link is None:
            self._variable = ControlVariable.get_class_for_type(value)(value)
        if not isinstance(value, self._variable._type_spec):
            raise TypeError("value type must match the linked control variable's type.")

        super().__init__(
            parent,
            command=action,
            takefocus=focusable,
            text=text,
            value=value,
            variable=self._variable,
            width=width,
        )

    def invoke(self) -> None:
        """Invoke this radiobutton, as if it had been clicked."""
        Tcl.call(None, self, "invoke")

    def select(self) -> None:
        """Select this radiobutton."""
        self._variable.set(self.value)

    @property
    def selected(self) -> bool:
        """Get or set whether this radiobutton is selected."""
        return self._variable.get() == self.value

    @property
    def value(self) -> float | str | bool:
        return cget(self, self._variable._type_spec, "-value")

    @value.setter
    def value(self, value: float | str | bool) -> None:
        if not isinstance(value, self._variable._type_spec):
            raise TypeError("value type must match the linked control variable's type.")

        config(self, value=value)


class RadioGroup:
    ...
