from __future__ import annotations

from functools import lru_cache, partialmethod
from typing import Callable, Iterable, Iterator, Union

from tukaan._collect import counter
from tukaan._tcl import Tcl
from tukaan._utils import instanceclassmethod
from tukaan.enums import BindingTag, EventQueue

from .events import Event, VirtualEvent, _virtual_event_data_container

EventHandlerType = Union[Callable[[], Union[None, bool]], Callable[[Event], Union[None, bool]]]


@lru_cache(maxsize=100)
def get_event_and_tcl_sequence(sequence: str) -> tuple[type[Event], str]:
    event = Event._get_type_for_sequence(sequence)
    return event, event._get_tcl_sequence(sequence)


def get_what_to_bind(widget_or_class) -> str:
    if not isinstance(widget_or_class, EventManager):
        return widget_or_class._tk_class_name
    if hasattr(widget_or_class, "_wm_path"):
        return widget_or_class._wm_path
    return widget_or_class._lm_path


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
    _wm_path: str
    _tk_class_name: str
    _bindings: dict[str, EventCallback] = {}

    def __init__(self):
        self._bindings = {}

    @instanceclassmethod
    def bind(
        self_or_cls,
        sequence: str,
        handler: EventHandlerType,
        *,
        overwrite: bool = False,
        send_event: bool = False,
    ) -> None:
        if "MouseWheel" in sequence and Tcl.windowing_system == "x11":
            # this can be removed with Tk 8.7
            for seq in ("Wheel:Up", "Wheel:Down"):
                self_or_cls.bind(
                    sequence.replace("MouseWheel", seq),
                    handler,
                    overwrite=overwrite,
                    send_event=send_event,
                )
            return

        if sequence not in self_or_cls._bindings:
            event, tcl_sequence = get_event_and_tcl_sequence(sequence)
            if not tcl_sequence:
                return

            event_callback = EventCallback(event, sequence)
            subst_str = " ".join(item[0] for item in event._subst.values())
            Tcl.call(
                None,
                "bind",
                get_what_to_bind(self_or_cls),
                tcl_sequence,
                f"+{Tcl.to(event_callback)} {subst_str}",
            )

            self_or_cls._bindings[sequence] = event_callback

        if overwrite:
            self_or_cls._bindings[sequence].clear()

        self_or_cls._bindings[sequence].add(handler, send_event)

    @instanceclassmethod
    def unbind(self_or_cls, sequence: str, handler: EventHandlerType):
        if sequence not in self_or_cls._bindings:
            return

        event_callback = self_or_cls._bindings[sequence]
        event_callback.remove(handler)

    @instanceclassmethod
    def get_event_handlers(self_or_cls, sequence: str) -> list[EventHandlerType]:
        if sequence not in self_or_cls._bindings:
            return []

        return self_or_cls._bindings[sequence]._handlers.copy()

    @property
    def binding_tags(self) -> tuple[BindingTag]:
        what = get_what_to_bind(self)
        result = []
        for tag in Tcl.call((str,), "bindtags", what):
            if tag == what:
                result.append(BindingTag.Instance)
            elif tag == self._tk_class_name:
                result.append(BindingTag.Class)
            elif tag == "all":
                result.append(BindingTag.Global)
            elif tag == Tcl.call(str, "winfo", "toplevel", what):
                result.append(BindingTag.Toplevel)

        return tuple(result)

    @binding_tags.setter
    def binding_tags(self, tags: Iterable):
        what = get_what_to_bind(self)
        result = []
        for tag in tags:
            if tag is BindingTag.Instance:
                result.append(what)
            elif tag is BindingTag.Class:
                result.append(self._tk_class_name)
            elif tag is BindingTag.Toplevel:
                result.append(Tcl.call(str, "winfo", "toplevel", what))
            elif tag is BindingTag.Global:
                result.append("all")

        Tcl.call(None, "bindtags", what, result)

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
    def __init__(self) -> None:
        self._event_info: dict[str, list[str]] = {}

    def _assign_os_unassign(self, method: str, sequence: str, events: str | list[str]) -> None:
        if isinstance(events, str):
            events = [events]

        if method == "add":
            self._event_info[sequence] = events
        elif sequence in self._event_info:
            self._event_info[sequence] = [
                item for item in self._event_info[sequence] if item not in set(events)
            ]
        else:
            # can't unassign nonexistent virtual event
            return

        if Tcl.windowing_system == "x11":
            to_be_replaced = {x for x in events if "MouseWheel" in x}
            for event in to_be_replaced:
                events.remove(event)
                for seq in ("Wheel:Up", "Wheel:Down"):
                    events.append(event.replace("MouseWheel", seq))

        tcl_sequences = [get_event_and_tcl_sequence(event)[1] for event in events]
        if not tcl_sequences:
            return

        Tcl.call(None, "event", method, sequence, *tcl_sequences)

    assign = partialmethod(_assign_os_unassign, "add")
    unassign = partialmethod(_assign_os_unassign, "delete")

    def __iter__(self) -> Iterator[str]:
        return iter(self._event_info.keys())

    def __getitem__(self, sequence: str) -> list[str] | None:
        return self._event_info.get(sequence)

    def __delitem__(self, sequence: str) -> None:
        self._event_info.pop(sequence, None)
        Tcl.call(None, "event", "delete", sequence, *Tcl.call([str], "event", "info", sequence))
