from __future__ import annotations

from typing import Callable, Union

from tukaan._collect import counter
from tukaan._tcl import Tcl

from .events import Event

EventHandlerType = Union[Callable[[], None | bool], Callable[[Event], None | bool]]


class EventCallback:
    _event: type[Event]
    _handlers: list[EventHandlerType]
    _send_event_to: list[EventHandlerType]

    def __init__(self, event: type[Event]) -> None:
        self._handlers = []
        self._send_event_to = []
        self._event = event

        self._name = name = f"tukaan_event_callback_{next(counter['events_callbacks'])}"
        Tcl._interp.createcommand(name, self.__call__)  # type: ignore

    def __call__(self, *args):
        if self._send_event_to:
            event = self._event(*args)

        for handler in self._handlers:
            if handler in self._send_event_to:
                handler(event)
            else:
                handler()

    def __len__(self) -> int:
        return len(self._handlers)

    def clear(self) -> None:
        self._handlers.clear()

    def add(self, handler: EventHandlerType, send_event: bool) -> None:
        self._handlers.append(handler)
        if send_event:
            self._send_event_to.append(handler)

    def remove(self, handler: EventHandlerType) -> None:
        self._handlers.remove(handler)
        self._send_event_to.remove(handler)

    def dispose(self) -> None:
        # TODO: figure out when it is safe to dispose a handler
        Tcl._interp.deletecommand(self._name)  # type: ignore


class EventManager:
    _bindings: dict[str, EventCallback]

    def __init__(self):
        self._bindings = {}

    def bind(
        self,
        sequence: str,
        handler: EventHandlerType,
        *,
        overwrite: bool = False,
        send_event: bool = False,
    ) -> None:
        if sequence not in self._bindings:
            event = Event._get_type_for_sequence(sequence)
            event_callback = EventCallback(event)
            subst_str = " ".join(item[0] for item in event._subst.values())
            tcl_sequence = event._get_tcl_sequence(sequence)
            if not tcl_sequence:
                event_callback.dispose()
                return
            Tcl.call(
                None,
                "bind",
                self,
                tcl_sequence,
                f"+{Tcl.to(event_callback)} {subst_str}",
            )

            self._bindings[sequence] = event_callback

        if overwrite:
            self._bindings[sequence].clear()

        self._bindings[sequence].add(handler, send_event)

    def unbind(self, sequence: str, handler: EventHandlerType):
        if sequence not in self._bindings:
            return

        event_callback = self._bindings[sequence]
        event_callback.remove(handler)

    def get_handlers(self) -> EventHandlerType:
        ...

    def generate_event(self):
        ...


class EventAliases:
    def assign(self, *args) -> None:
        ...

    def unassign(self, *args) -> None:
        ...

    def __getitem__(self, sequence: str) -> list[str] | None:
        ...

    def __delitem__(self, sequence: str) -> None:
        ...
