from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional

from tukaan._misc import Time, _Time
from tukaan._utils import _sounds, counts, get_tcl_interp, py_to_tcl_args
from tukaan.exceptions import TclError


class BaseFilter:
    def __and__(self, other):
        if isinstance(other, ComposeFilter):
            other.append(self)
            return other
        return ComposeFilter(self, other)

    def to_tcl(self):
        return self._name

    def delete(self):
        get_tcl_interp()._tcl_call(None, self._name, "destroy")

    def __enter__(self):
        AudioDevice._current_context_filter = self
        return self

    def __exit__(self, exc_type, exc_value, _):
        AudioDevice._current_context_filter = None

        if exc_type is not None:
            raise exc_type(exc_value) from None


class ComposeFilter(BaseFilter):
    def __init__(self, filter_1, filter_2):
        self._filters = [filter_1, filter_2]

        self._name = get_tcl_interp()._tcl_call(str, "Snack::filter", "compose", filter_1, filter_2)

    def append(self, filter: BaseFilter):
        self._filters.append(filter)
        get_tcl_interp()._tcl_call(None, self, "configure", *self._filters)

    def __and__(self, other):
        self.append(other)
        return self

    def to_tcl(self):
        return self._name


class AmplifierFilter(BaseFilter):
    # Echo with 0 delay is the easiest way to amplify sound
    def __init__(self, volume: float = 150):
        self._name = get_tcl_interp()._tcl_call(str, "Snack::filter", "echo", 1, volume / 100, 1, 0)


class EchoFilter(BaseFilter):
    def __init__(
        self,
        delay: float = 0.5,
        decay_factor: float = 0.5,
        gain_in: float = 1,
        gain_out: float = 1,
    ):
        if delay < 0.001:
            delay = 0.001

        self._name = get_tcl_interp()._tcl_call(
            str, "Snack::filter", "echo", gain_in, gain_out, delay * 1000, decay_factor
        )


class FadeInFilter(BaseFilter):
    def __init__(self, length: float = 5, type: str = "linear") -> None:
        self._name = get_tcl_interp()._tcl_call(
            str, "Snack::filter", "fade", "in", type, length * 1000
        )


class FadeOutFilter(BaseFilter):
    def __init__(self, length: float = 5, type: str = "linear") -> None:
        self._name = get_tcl_interp()._tcl_call(
            str, "Snack::filter", "fade", "out", type, length * 1000
        )


class FormantFilter(BaseFilter):
    def __init__(self, frequency: float, bandwidth: int) -> None:
        self._name = get_tcl_interp()._tcl_call(
            str, "Snack::filter", "formant", frequency, bandwidth
        )


class GeneratorFilter(BaseFilter):
    def __init__(
        self, frequency: float, amplitude: int, shape: float = 0.5, type: str = "sine"
    ) -> None:
        self._name = get_tcl_interp()._tcl_call(
            str, "Snack::filter", "generator", frequency, amplitude, shape, type
        )


class IIRFilter(BaseFilter):
    def __init__(
        self,
        denom: list = [1],
        numer: list = [1],
        dither: float = 1,
        impulse: list = [1, 2],
        noise: float = 1,
    ):

        self._name = get_tcl_interp()._tcl_call(
            str,
            "Snack::filter",
            "iir",
            *py_to_tcl_args(
                denominator=denom,
                dither=dither,
                impulse=impulse,
                noise=noise,
                numerator=numer,
            ),
        )


class MapFilter(BaseFilter):
    def __init__(self, *args):
        self._name = get_tcl_interp()._tcl_call(
            str, "Snack::filter", "map", *(x / 100 for x in args)
        )


class ReverbFilter(BaseFilter):
    def __init__(self, time: float = 5, delay: float = 1, volume: float = 100):
        if time < 0.001:
            time = 0.001

        if delay < 0.001:
            delay = 0.001

        self._name = get_tcl_interp()._tcl_call(
            str, "Snack::filter", "reverb", volume / 100, time * 1000, delay * 1000
        )


class Filter:
    Amplifier = AmplifierFilter
    Echo = EchoFilter
    FadeIn = FadeInFilter
    FadeOut = FadeOutFilter
    Formant = FormantFilter
    Generator = GeneratorFilter
    IIR = IIRFilter
    Map = MapFilter
    Reverb = ReverbFilter


class Sound:
    def __init__(
        self,
        file=None,
        format: Optional[str] = None,
        *,
        bitrate: int = None,
        buffer_size: Optional[float] = None,
        byteorder: Optional[str] = None,
        channels: Optional[int] = None,
        encoding: Optional[str] = None,
        guess_properties: Optional[bool] = None,
        precision: Optional[str] = None,
    ):
        self._interp = get_tcl_interp()
        self._name = f"tukaan_sound_{next(counts['sounds'])}"

        self._interp._tcl_call(
            None,
            "Snack::sound",
            self._name,
            *py_to_tcl_args(
                buffersize=buffer_size,
                byteorder=byteorder,
                channels=channels,
                encoding=encoding,
                fileformat=format,
                guessproperties=guess_properties,
                load=file,
                precision=precision,
                rate=bitrate,
            ),
        )
        _sounds[self._name] = self

    def to_tcl(self):
        # to_tcl is provided for compatibility reasons, i don't use because of performance
        return self._name

    def _get_sample(self, time):
        return time.total_seconds * self.bitrate

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, _):
        if exc_type is None:
            try:
                self.delete()
            except TclError:
                # already deleted
                pass
        else:
            raise exc_type(exc_value) from None

    def __len__(self) -> int:
        return int(
            round(
                self._interp._tcl_call(float, self._name, "length", "-unit", "seconds"),
                0,
            )
        )

    def __getitem__(self, key: slice) -> SoundSection:
        if isinstance(key, slice):
            return SoundSection(self, key)
        raise TypeError("should be a slice. Like sound[3.14:] instead of sound[3.14]")

    def __delitem__(self, key: slice) -> None:
        if isinstance(key, slice):
            start, end = key.start, key.stop

            if isinstance(start, Time):
                start = int(start.total_seconds * self.bitrate)
            if isinstance(end, Time):
                end = int(end.total_seconds * self.bitrate)

            if start is None:
                start = 0
            if end is None:
                end = self._interp._tcl_call(int, self._name, "length") - 1

            return self._interp._tcl_call(None, self._name, "cut", start, end)

        raise TypeError("should be a slice. Like sound[3.14:] instead of sound[3.14]")

    def play(
        self,
        start_time=None,
        *,
        after=None,
        block=None,
        on_end: Callable = None,
        output=None,
        repeat=False,
    ):
        if after is not None:
            after *= 1000

        if isinstance(start_time, Time):
            start_time = self._get_sample(start_time)

        filter_ = AudioDevice._current_context_filter

        self._interp._tcl_call(
            None,
            self._name,
            "play",
            *py_to_tcl_args(
                blocking=block,
                command=on_end,
                device=output,
                filter=filter_,
                start=start_time,
                starttime=after,
            ),
        )

    def pause(self):
        self._interp._tcl_call(None, self._name, "pause")

    def stop(self):
        self._interp._tcl_call(None, self._name, "stop")

    @contextmanager
    def record(self, input="default", overwrite=True):
        if overwrite:
            self.stop()

        self._interp._tcl_call(
            None, self._name, "record", "-device", input, "-append", not overwrite
        )

        try:
            yield
        finally:
            self.stop()

    def start_recording(self, input="default", overwrite=True):
        if overwrite:
            self.stop()

        self._interp._tcl_call(
            None, self._name, "record", "-device", input, "-append", not overwrite
        )

    def save(self, file_name: str | Path, format: str = None, *, byteorder: str = None) -> None:
        self._interp._tcl_call(
            None,
            self._name,
            "write",
            file_name,
            *py_to_tcl_args(byteorder=byteorder, fileformat=format),
        )

    def load(
        self,
        file_name: str | Path,
        format: Optional[str] = None,
        *,
        bitrate: int = 44100,
        buffer_size: Optional[float] = None,
        byteorder: Optional[str] = None,
        channels: Optional[int] = None,
        encoding: Optional[str] = None,
        guess_properties: Optional[bool] = None,
        precision: Optional[str] = None,
    ) -> None:
        self._interp._tcl_call(
            None,
            self._name,
            "read",
            file_name,
            *py_to_tcl_args(
                buffersize=buffer_size,
                byteorder=byteorder,
                channels=channels,
                fileformat=format,
                encoding=encoding,
                guessproperties=guess_properties,
                precision=precision,
                rate=bitrate,
            ),
        )

    def convert(
        self,
        arg: Optional[str | int] = None,
        *,
        bitrate: Optional[int] = None,
        encoding: Optional[str] = None,
        channels: Optional[int] = None,
    ):
        if arg is not None:
            if arg in {"mono", "stereo"}:
                channels = arg
            elif arg in {8000, 11025, 16000, 22050, 32000, 44100, 48000}:
                bitrate = arg
            elif arg in {
                "Lin16",
                "Lin8offset",
                "Lin8",
                "Lin24",
                "Lin32",
                "Float",
                "Alaw",
                "Mulaw",
            }:
                encoding = arg
            else:
                raise ValueError(f"invalid argument: {arg}")

        self._interp._tcl_call(
            None,
            self,
            "convert",
            *py_to_tcl_args(rate=bitrate, encoding=encoding, channels=channels),
        )
        return self

    def copy(self):
        new_sound = Sound()
        self._interp._tcl_call(None, new_sound._name, "copy", self._name)
        return new_sound

    def apply_filter(self, filter: BaseFilter) -> Sound:
        self._interp._tcl_call(None, self._name, "filter", filter._name)
        return self

    __imatmul__ = apply_filter

    def __iadd__(self, other_sound: Sound) -> Sound:
        if isinstance(other_sound, SoundSection):
            other_sound = other_sound.copy()

        self._interp._tcl_call(None, self._name, "concatenate", other_sound._name)
        return self

    def __iand__(self, other_sound: Sound | SoundSection) -> Sound:
        if isinstance(other_sound, SoundSection):
            self._interp._tcl_call(
                None,
                self._name,
                "mix",
                other_sound._name,
                *py_to_tcl_args(start=other_sound.start, end=other_sound.end),
            )
        else:
            self._interp._tcl_call(None, self._name, "mix", other_sound._name)
        return self

    def insert(self, position, other_sound) -> Sound:
        if isinstance(position, Time):
            position = self._get_sample(position)

        if isinstance(other_sound, SoundSection):
            self._interp._tcl_call(
                None,
                self._name,
                "insert",
                other_sound._name,
                position,
                *py_to_tcl_args(start=other_sound.start, end=other_sound.end),
            )
        else:
            self._interp._tcl_call(
                None,
                self._name,
                "insert",
                other_sound._name,
                position,
            )
        return self

    def reverse(self) -> Sound:
        self._interp._tcl_call(None, self._name, "reverse")
        return self

    def get_pitch(
        self,
        method="amdf",
        *,
        frame_length=None,
        window_length=None,
        max=None,
        min=None,
    ):
        if method == "amdf":
            type_spec = [float]
        elif method == "esps":
            type_spec = [(float,)]
        else:
            raise ValueError(f"invalid pitch method: {method}. Should be either 'amdf' or 'esps'")

        return self._interp._tcl_call(
            type_spec,
            self._name,
            "pitch",
            "-method",
            "amdf",
            *py_to_tcl_args(
                framelength=frame_length,
                windowlength=window_length,
                minpitch=min,
                maxpitch=max,
            ),
        )

    def flush(self):
        self._interp._tcl_call(None, self._name, "flush")

    def delete(self):
        self._interp._tcl_call(None, self._name, "destroy")
        del _sounds[self._name]

    def _get(self, type_spec, key):
        return self._interp._tcl_call(type_spec, self._name, "cget", f"-{key}")

    def config(
        self,
        *,
        buffer_size=None,
        channels=None,
        encoding=None,
        precision=None,
        bitrate=None,
    ):
        return self._interp._tcl_call(
            None,
            self._name,
            "configure",
            *py_to_tcl_args(
                buffersize=buffer_size,
                channels=channels,
                encoding=encoding,
                precision=precision,
                rate=bitrate,
            ),
        )

    @property
    def length(self) -> float:
        return _Time.from_secs(
            self._interp._tcl_call(float, self._name, "length", "-unit", "seconds")
        )

    @length.setter
    def length(self, new_length: float) -> None:
        if isinstance(new_length, Time):
            new_length = new_length.total_seconds

        self._interp._tcl_call(None, self._name, "length", new_length, "-unit", "seconds")

    @property
    def bitrate(self) -> int:
        return self._get(int, "rate")

    @bitrate.setter
    def bitrate(self, new_bitrate: int) -> None:
        return self.config(bitrate=new_bitrate)

    @property
    def buffer_size(self) -> float:
        return self._get(float, "buffersize")

    @buffer_size.setter
    def buffer_size(self, new_buffer_size: float) -> None:
        return self.config(buffer_size=new_buffer_size)

    @property
    def channels(self) -> int:
        return self._get(int, "channels")

    @channels.setter
    def channels(self, new_channels: float) -> None:
        return self.config(channels=new_channels)

    @property
    def encoding(self) -> str:
        return self._get(str, "encoding")

    @encoding.setter
    def encoding(self, new_encoding: float) -> None:
        return self.config(encoding=new_encoding)

    @property
    def precision(self) -> str:
        return self._get(str, "precision")

    @precision.setter
    def precision(self, new_precision: str) -> None:
        return self.config(encoding=new_precision)


class SoundSection:
    def __init__(self, sound, slice_arg):
        self._name = sound._name
        self._sound = sound
        bitrate = get_tcl_interp()._tcl_call(int, self._name, "cget", "-rate")

        start, end = slice_arg.start, slice_arg.stop

        if isinstance(start, Time):
            start = int(start.total_seconds * bitrate)

        if isinstance(end, Time):
            end = int(end.total_seconds * bitrate)

        if start is None:
            start = 0
        if end is None:
            end = get_tcl_interp()._tcl_call(int, self._name, "length") - 1

        self.start, self.end = start, end
        self.length = Time(seconds=end / bitrate - start / bitrate)

    def play(
        self,
        *,
        after=None,
        block=None,
        on_end: Callable = None,
        output=None,
        repeat=False,
    ):
        if after is not None:
            after *= 1000

        filter_ = AudioDevice._current_context_filter

        get_tcl_interp()._tcl_call(
            None,
            self._name,
            "play",
            *py_to_tcl_args(
                blocking=block,
                command=on_end,
                device=output,
                filter=filter_,
                start=self.start,
                end=self.end,
                starttime=after,
            ),
        )

    def save(self, file_name: str | Path, format: str = None, *, byteorder: str = None) -> None:
        get_tcl_interp()._tcl_call(
            None,
            self._name,
            "write",
            file_name,
            *py_to_tcl_args(start=self.start, end=self.end, byteorder=byteorder, fileformat=format),
        )

    @property
    def detached(self):
        new_sound = Sound()
        get_tcl_interp()._tcl_call(
            None,
            new_sound._name,
            "copy",
            self._name,
            *py_to_tcl_args(start=self.start, end=self.end),
        )
        return new_sound

    def apply_filter(self, filter: BaseFilter) -> Sound:
        get_tcl_interp()._tcl_call(
            None,
            self._name,
            "filter",
            filter._name,
            *py_to_tcl_args(start=self.start, end=self.end),
        )
        return self._sound

    __imatmul__ = apply_filter

    def crop(self):
        get_tcl_interp()._tcl_call(None, self._name, "crop", self.start, self.end)
        return self._sound

    def cut(self):
        get_tcl_interp()._tcl_call(None, self._name, "cut", self.start, self.end)
        return self._sound

    def reverse(self):
        get_tcl_interp()._tcl_call(
            None,
            self._name,
            "reverse",
            *py_to_tcl_args(start=self.start, end=self.end),
        )
        return self._sound

    def get_pitch(
        self,
        method="amdf",
        *,
        frame_length=None,
        window_length=None,
        max=None,
        min=None,
    ):
        args = py_to_tcl_args(
            end=self.end,
            framelength=frame_length,
            maxpitch=max,
            minpitch=min,
            start=self.start,
            windowlength=window_length,
        )

        if method == "amdf":
            return get_tcl_interp()._tcl_call(
                [float], self._name, "pitch", "-method", "amdf", *args
            )
        elif method == "esps":
            return get_tcl_interp()._tcl_call(
                [(float,)], self._name, "pitch", "-method", "esps", *args
            )
        else:
            raise ValueError(f"invalid pitch method: {method}. Should be either 'amdf' or 'esps'")


class _AudioDevice:
    _current_input = "default"
    _current_output = "default"
    _current_context_filter = None

    @property
    def supported_encodings(self) -> list[str]:
        return get_tcl_interp()._tcl_call([str], "Snack::audio", "encodings")

    @property
    def supported_bitrates(self) -> list[str]:
        return get_tcl_interp()._tcl_call([int], "Snack::audio", "rates")

    @property
    def latency(self) -> float:
        return get_tcl_interp()._tcl_call(float, "Snack::audio", "playLatency") / 1000

    @latency.setter
    def latency(self, new_latency: float) -> None:
        get_tcl_interp()._tcl_call(None, "Snack::audio", "playLatency", new_latency * 1000)

    @property
    def inputs(self) -> list[str]:
        return get_tcl_interp()._tcl_call([str], "Snack::audio", "inputDevices")

    @property
    def outputs(self) -> list[str]:
        return get_tcl_interp()._tcl_call([str], "Snack::audio", "outputDevices")

    @property
    def default_input(self) -> str:
        return self._current_input

    @default_input.setter
    def default_input(self, device: str) -> str:
        self._current_input = device
        return get_tcl_interp()._tcl_call(None, "Snack::audio", "selectInput", device)

    @property
    def default_output(self) -> str:
        return self._current_output

    @default_output.setter
    def default_output(self, device: str) -> str:
        self._current_output = device
        return get_tcl_interp()._tcl_call(None, "Snack::audio", "selectOutput", device)

    @property
    def is_playing(self) -> bool:
        return get_tcl_interp()._tcl_call(bool, "Snack::audio", "active")

    def resume_all(self) -> None:
        return get_tcl_interp()._tcl_call(None, "Snack::audio", "play")

    def pause_all(self) -> None:
        return get_tcl_interp()._tcl_call(None, "Snack::audio", "pause")

    def stop_all(self) -> None:
        return get_tcl_interp()._tcl_call(None, "Snack::audio", "stop")


AudioDevice = _AudioDevice()
