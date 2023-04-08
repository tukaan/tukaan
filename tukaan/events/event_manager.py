from __future__ import annotations

from typing import Callable, Iterator, Union

from tukaan._collect import counter
from tukaan._tcl import Tcl
from tukaan.enums import EventQueue
from functools import lru_cache, partialmethod

from .events import Event, _virtual_event_data_container, VirtualEvent

EventHandlerType = Union[Callable[[], None | bool], Callable[[Event], None | bool]]


@lru_cache(maxsize=100)
def get_event_and_tcl_sequence(sequence: str) -> tuple[type[Event], str]:
    event = Event._get_type_for_sequence(sequence)
    return event, event._get_tcl_sequence(sequence)


class EventCallback:
    _event: type[Event]
    _handlers: list[EventHandlerType]
    _send_event_to: list[EventHandlerType]

    def __init__(self, event: type[Event], sequence: str) -> None:
        self._handlers = []
        self._send_event_to = []
        self._event = event
        self._sequence = sequence

        self._name = name = f"tukaan_event_callback_{next(counter['events_callbacks'])}"
        Tcl._interp.createcommand(name, self.__call__)  # type: ignore

    def __call__(self, *args):
        if self._send_event_to:
            event = self._event(*args)
            event.sequence = self._sequence

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
        if handler in self._handlers:
            self._handlers.remove(handler)

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
    _lm_path: str
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
        if "MouseWheel" in sequence and Tcl.windowing_system == "x11":
            # this can be removed with Tk 8.7
            for seq in ("Wheel:Up", "Wheel:Down"):
                self.bind(
                    sequence.replace("MouseWheel", seq),
                    handler,
                    overwrite=overwrite,
                    send_event=send_event,
                )
            return

        if sequence not in self._bindings:
            event, tcl_sequence = get_event_and_tcl_sequence(sequence)
            if not tcl_sequence:
                return

            event_callback = EventCallback(event, sequence)
            subst_str = " ".join(item[0] for item in event._subst.values())
            Tcl.call(
                None,
                "bind",
                self._lm_path,
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

    def get_event_handlers(self, sequence: str) -> list[EventHandlerType]:
        if sequence not in self._bindings:
            return []

        return self._bindings[sequence]._handlers.copy()

    def generate_event(self, sequence: str, data: object = None, queue: EventQueue = None) -> None:
        if not VirtualEvent._matches(sequence):
            raise Exception("can only generate virtual events")

        key = None if data is None else _virtual_event_data_container.add(data)
        Tcl.call(
            None,
            "event",
            "generate",
            self._lm_path,
            sequence,
            *Tcl.to_tcl_args(data=key, when=queue),
        )


class EventAliases:
    def _assign_os_unassign(self, method: str, sequence: str, events: str | list[str]) -> None:
        if isinstance(events, str):
            events = [events]

        tcl_sequences = [get_event_and_tcl_sequence(event)[1] for event in events]
        if not tcl_sequences:
            return

        Tcl.call(None, "event", method, sequence, *tcl_sequences)

    assign = partialmethod(_assign_os_unassign, "add")
    unassign = partialmethod(_assign_os_unassign, "delete")

    def __iter__(self) -> Iterator[str]:
        return iter(Tcl.call([str], "event", "info"))

    def __getitem__(self, sequence: str) -> list[str] | None:
        # TODO: convert tcl binding sequences back to tukaan ones
        return Tcl.call([str], "event", "info", sequence) or None

    def __delitem__(self, sequence: str) -> None:
        Tcl.call(None, "event", "delete", sequence, *Tcl.call([str], "event", "info", sequence))
