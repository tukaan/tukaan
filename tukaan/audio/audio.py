from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from tukaan._tcl import Tcl
from tukaan._utils import _sounds, counts
from tukaan.exceptions import TclError
from tukaan.time import Time, TimeConstructor


### Enums ###
class Format(Enum):
    AIFF = "aiff"
    AU = "au"
    SD = "sd"
    SMP = "smp"
    SND = "snd"
    CSL = "csl"
    WAV = "wav"
    RAW = "raw"


class Encoding(Enum):
    Alaw = "Alaw"
    Float = "Float"
    Lin16 = "Lin16"
    Lin24 = "Lin24"
    Lin32 = "Lin32"
    Lin8 = "Lin8"
    Lin8_Offset = "Lin8offset"
    Mulaw = "Mulaw"


class ByteOrder(Enum):
    BigEndian = "BigEndian"
    LittleEndian = "LittleEndian"


class Precision(Enum):
    Double = "double"
    Single = "single"


class PitchMethod(Enum):
    AMDF = "amdf"
    ESPS = "esps"


### Filters ###
class Filter:
    def __init_subclass__(cls):
        setattr(Filter, cls.__name__.replace("Filter", ""), cls)

    def __and__(self, other):
        if isinstance(other, ComposeFilter):
            other.append(self)
            return other
        return ComposeFilter(self, other)

    def __enter__(self):
        Device._current_context_filter = self
        return self

    def __exit__(self, exc_type, exc_value, _):
        Device._current_context_filter = None

        if exc_type is not None:
            raise exc_type(exc_value) from None

    def __to_tcl__(self):
        return self._name

    def delete(self):
        Tcl.call(None, self, "destroy")


class ComposeFilter(Filter):
    def __init__(self, filter_1, filter_2, /):
        self._filters = [filter_1, filter_2]

        self._name = Tcl.call(str, "Snack::filter", "compose", filter_1, filter_2)

    def __and__(self, other):
        self.append(other)
        return self

    def append(self, filt: Filter, /):
        self._filters.append(filt)
        Tcl.call(None, self, "configure", *self._filters)


class AmplifierFilter(Filter):
    # Echo with 0 delay is the easiest way to amplify sound
    def __init__(self, volume: float = 125):
        self._name = Tcl.call(str, "Snack::filter", "echo", 1, volume / 100, 1, 0)


class EchoFilter(Filter):
    def __init__(
        self,
        delay: float = 0.5,
        decay_factor: float = 0.5,
        gain_in: float = 0.5,
        gain_out: float = 0.5,
    ):
        if delay < 0.001:
            delay = 0.001

        self._name = Tcl.call(
            str, "Snack::filter", "echo", gain_in, gain_out, delay * 1000, decay_factor
        )


class FadeInFilter(Filter):
    def __init__(self, length: float = 5, type: str = "linear") -> None:
        self._name = Tcl.call(str, "Snack::filter", "fade", "in", type, length * 1000)


class FadeOutFilter(Filter):
    def __init__(self, length: float = 5, type: str = "linear") -> None:
        self._name = Tcl.call(str, "Snack::filter", "fade", "out", type, length * 1000)


class FormantFilter(Filter):
    def __init__(self, frequency: float, bandwidth: int) -> None:
        self._name = Tcl.call(str, "Snack::filter", "formant", frequency, bandwidth)


class GeneratorFilter(Filter):
    def __init__(
        self,
        frequency: float,
        amplitude: int,
        type: str = "sine",
        *,
        shape: float = 0.5,
    ) -> None:
        self._name = Tcl.call(str, "Snack::filter", "generator", frequency, amplitude, shape, type)


class IIRFilter(Filter):
    def __init__(
        self,
        *,
        denom: list[float] = [1],
        numer: list[float] = [1],
        dither: float = 1,
        impulse: list[float] = [1, 2],
        noise: float = 1,
    ):

        self._name = Tcl.call(
            str,
            "Snack::filter",
            "iir",
            *Tcl.to_tcl_args(
                denominator=denom,
                dither=dither,
                impulse=impulse,
                noise=noise,
                numerator=numer,
            ),
        )


class MixChannelsFilter(Filter):
    def __init__(
        self,
        left_to_left: int = 0,
        right_to_left: int = 0,
        left_to_right: int = 0,
        right_to_right: int = 0,
    ):
        self._name = Tcl.call(
            str,
            "Snack::filter",
            "map",
            left_to_left / 100,
            right_to_left / 100,
            left_to_right / 100,
            right_to_right / 100,
        )


class ReverbFilter(Filter):
    def __init__(self, time: float = 5, delay: float = 1, volume: float = 100):
        if time < 0.001:
            time = 0.001

        if delay < 0.001:
            delay = 0.001

        self._name = Tcl.call(
            str, "Snack::filter", "reverb", volume / 100, time * 1000, delay * 1000
        )


### Sound ###
class Sound:
    def __init__(
        self,
        file: Path | str | None = None,
        format: str | None = None,
        *,
        buffer_size: float | None = None,
        byteorder: ByteOrder | None = None,
        channels: int | None = None,
        encoding: str | Encoding | None = None,
        guess_properties: bool | None = None,
        precision: Precision | None = None,
        sample_rate: int = None,
    ):
        self._name = f"tukaan_sound_{next(counts['sounds'])}"

        Tcl.call(
            None,
            "Snack::sound",
            self,
            *Tcl.to_tcl_args(
                buffersize=buffer_size,
                byteorder=byteorder,
                channels=channels,
                encoding=encoding,
                fileformat=format,
                guessproperties=guess_properties,
                load=file,
                precision=precision,
                rate=sample_rate,
            ),
        )
        _sounds[self._name] = self

    def _get_sample(self, time):
        return time.total_seconds * self.sample_rate

    def __to_tcl__(self):
        return self._name

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
                Tcl.call(float, self, "length", "-unit", "seconds"),
                0,
            )
        )

    def __getitem__(self, key: slice) -> SoundSection:
        if isinstance(key, slice):
            return SoundSection(self, key)
        raise TypeError("should be a slice. Like sound[Time[3.14]:] instead of sound[Time[3.14]]")

    def __delitem__(self, key: slice) -> None:
        if not isinstance(key, slice):
            raise TypeError(
                "should be a slice. Like sound[Time[3.14]:] instead of sound[Time[3.14]]"
            )

        start, end = key.start, key.stop

        if isinstance(start, Time):
            start = int(start.total_seconds * self.sample_rate)

        if isinstance(end, Time):
            end = int(end.total_seconds * self.sample_rate)

        if start in {None, ...}:
            start = 0

        if end in {None, ...}:
            end = Tcl.call(int, self, "length") - 1

        return Tcl.call(None, self, "cut", start, end)

    def play(
        self,
        start_time: int | Time | None = None,
        *,
        after: int | Time | None = None,
        block: bool | None = None,
        on_end: Callable = None,
        output: str | None = None,
    ) -> Sound:
        if after is not None:
            after *= 1000

        if isinstance(start_time, Time):
            start_time = self._get_sample(start_time)

        filter_ = Device._current_context_filter

        Tcl.call(
            None,
            self,
            "play",
            *Tcl.to_tcl_args(
                blocking=block,
                command=on_end,
                device=output,
                filter=filter_,
                start=start_time,
                starttime=after,
            ),
        )
        return self

    def pause(self) -> Sound:
        Tcl.call(None, self, "pause")
        return self

    def stop(self) -> Sound:
        Tcl.call(None, self, "stop")
        return self

    @contextmanager
    def record(self, input: str = "default", overwrite: bool = True) -> None:
        if overwrite:
            self.stop()

        Tcl.call(None, self, "record", "-device", input, "-append", not overwrite)

        try:
            yield
        finally:
            self.stop()

    def start_recording(self, input: str = "default", overwrite: bool = True) -> Sound:
        if overwrite:
            self.stop()

        Tcl.call(None, self, "record", "-device", input, "-append", not overwrite)
        return self

    def save(
        self,
        file_name: str | Path,
        format: str | Format | None = None,
        *,
        byteorder: ByteOrder | None = None,
    ) -> Sound:
        Tcl.call(
            None,
            self,
            "write",
            file_name,
            *Tcl.to_tcl_args(byteorder=byteorder, fileformat=format),
        )
        return self

    def load(
        self,
        file_name: str | Path,
        format: str | None = None,
        *,
        sample_rate: int | None = None,
        buffer_size: float | None = None,
        byteorder: ByteOrder | None = None,
        channels: int | None = None,
        encoding: str | Encoding | None = None,
        guess_properties: bool | None = None,
        precision: Precision | None = None,
    ) -> Sound:
        Tcl.call(
            None,
            self,
            "read",
            file_name,
            *Tcl.to_tcl_args(
                buffersize=buffer_size,
                byteorder=byteorder,
                channels=channels,
                fileformat=format,
                encoding=encoding,
                guessproperties=guess_properties,
                precision=precision,
                rate=sample_rate,
            ),
        )
        return self

    def convert(
        self,
        arg: str | int | Encoding | None = None,
        /,
        *,
        sample_rate: int | None = None,
        encoding: str | None = None,
        channels: int | None = None,
    ) -> Sound:
        if arg is not None:
            if arg in {"mono", "stereo"}:
                channels = arg
            elif arg in {8000, 11025, 16000, 22050, 32000, 44100, 48000}:
                sample_rate = arg
            elif arg in Encoding:
                encoding = arg
            else:
                raise ValueError(f"invalid positional argument: {arg}")

        Tcl.call(
            None,
            self,
            "convert",
            *Tcl.to_tcl_args(rate=sample_rate, encoding=encoding, channels=channels),
        )
        return self

    def copy(self) -> Sound:
        new_sound = Sound()
        Tcl.call(None, new_sound, "copy", self)
        return new_sound

    def filter(self, filter_: Filter, /) -> Sound:
        Tcl.call(None, self, "filter", filter_)
        return self

    __imatmul__ = filter

    def concat(self, other_sound: Sound, /) -> Sound:
        if isinstance(other_sound, SoundSection):
            other_sound = other_sound.copy()

        Tcl.call(None, self, "concatenate", other_sound)
        return self

    __iadd__ = concat

    def mix(self, other_sound: Sound | SoundSection, /) -> Sound:
        args = ()
        if isinstance(other_sound, SoundSection):
            args = (*Tcl.to_tcl_args(start=other_sound.start, end=other_sound.end),)

        Tcl.call(None, self, "mix", other_sound, *args)
        return self

    __iand__ = mix

    def insert(self, position: int | Time, other_sound: Sound | SoundSection, /) -> Sound:
        if isinstance(position, Time):
            position = self._get_sample(position)

        args = ()
        if isinstance(other_sound, SoundSection):
            args = (*Tcl.to_tcl_args(start=other_sound.start, end=other_sound.end),)

        Tcl.call(None, self, "insert", other_sound, position, *args)
        return self

    def reverse(self) -> Sound:
        Tcl.call(None, self, "reverse")
        return self

    __reversed__ = reverse

    def get_pitch(
        self,
        method: PitchMethod = PitchMethod.AMDF,
        *,
        frame_length: float | None = None,
        window_length: float | None = None,
        max: float | None = None,
        min: float | None = None,
    ) -> list[float] | list[tuple[float, float, float, float]]:
        if method is PitchMethod.AMDF:
            return_type = [float]
        elif method is PitchMethod.ESPS:
            return_type = [(float,)]

        return Tcl.call(
            return_type,
            self,
            "pitch",
            "-method",
            method,
            *Tcl.to_tcl_args(
                framelength=frame_length,
                maxpitch=max,
                minpitch=min,
                windowlength=window_length,
            ),
        )

    def flush(self) -> Sound:
        Tcl.call(None, self, "flush")
        return self

    def delete(self) -> None:
        Tcl.call(None, self, "destroy")
        del _sounds[self]

    def _get(self, type_spec: Any, key: str) -> Any:
        return Tcl.call(type_spec, self, "cget", f"-{key}")

    def config(
        self,
        *,
        buffer_size: float | None = None,
        channels: str | int | None = None,
        encoding: str | Encoding | None = None,
        precision: Precision | None = None,
        sample_rate=None,
    ) -> Sound:
        Tcl.call(
            None,
            self,
            "configure",
            *Tcl.to_tcl_args(
                buffersize=buffer_size,
                channels=channels,
                encoding=encoding,
                precision=precision,
                rate=sample_rate,
            ),
        )
        return self

    @property
    def length(self) -> float:
        return TimeConstructor.from_secs(Tcl.call(float, self, "length", "-unit", "seconds"))

    @length.setter
    def length(self, new_length: float) -> None:
        if isinstance(new_length, Time):
            new_length = new_length.total_seconds

        Tcl.call(None, self, "length", new_length, "-unit", "seconds")

    @property
    def sample_rate(self) -> int:
        return self._get(int, "rate")

    @sample_rate.setter
    def sample_rate(self, new_sample_rate: int) -> None:
        return self.config(sample_rate=new_sample_rate)

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
    def precision(self, new_precision: Precision) -> None:
        return self.config(encoding=new_precision)


class SoundSection:
    def __init__(self, sound: Sound, slice_arg: slice, /) -> None:
        self._name = sound._name
        self._sound = sound
        sample_rate = Tcl.call(int, self, "cget", "-rate")

        start, end = slice_arg.start, slice_arg.stop

        if isinstance(start, Time):
            start = int(start.total_seconds * sample_rate)

        if isinstance(end, Time):
            end = int(end.total_seconds * sample_rate)

        if start in {None, ...}:
            start = 0

        if end in {None, ...}:
            end = Tcl.call(int, self, "length") - 1

        self.start, self.end = start, end
        self.length = Time(seconds=end / sample_rate - start / sample_rate)

    def play(
        self,
        *,
        after: int | Time | None = None,
        block: bool | None = None,
        on_end: Callable = None,
        output: str | None = None,
    ) -> SoundSection:
        if after is not None:
            after *= 1000

        filter_ = Device._current_context_filter

        Tcl.call(
            None,
            self,
            "play",
            *Tcl.to_tcl_args(
                blocking=block,
                command=on_end,
                device=output,
                end=self.end,
                filter=filter_,
                start=self.start,
                starttime=after,
            ),
        )
        return self

    def save(
        self,
        file_name: str | Path,
        format: str | Format | None = None,
        *,
        byteorder: ByteOrder | None = None,
    ) -> SoundSection:
        Tcl.call(
            None,
            self,
            "write",
            file_name,
            *Tcl.to_tcl_args(
                start=self.start, end=self.end, byteorder=byteorder, fileformat=format
            ),
        )
        return self

    @property
    def detached(self) -> Sound:
        new_sound = Sound()
        Tcl.call(
            None,
            new_sound,
            "copy",
            self,
            *Tcl.to_tcl_args(start=self.start, end=self.end),
        )
        return new_sound

    def filter(self, filter_: Filter, /) -> SoundSection:
        Tcl.call(
            None,
            self,
            "filter",
            filter_,
            *Tcl.to_tcl_args(start=self.start, end=self.end),
        )
        return self

    __imatmul__ = filter

    def crop(self) -> SoundSection:
        Tcl.call(None, self, "crop", self.start, self.end)
        return self

    def cut(self) -> SoundSection:
        Tcl.call(None, self, "cut", self.start, self.end)
        return self

    def reverse(self) -> SoundSection:
        Tcl.call(None, self, "reverse", *Tcl.to_tcl_args(start=self.start, end=self.end))
        return self

    __reversed__ = reverse

    def get_pitch(
        self,
        method: PitchMethod = PitchMethod.AMDF,
        *,
        frame_length: float | None = None,
        max: float | None = None,
        min: float | None = None,
        window_length: float | None = None,
    ) -> list[float] | list[tuple[float, float, float, float]]:
        if method is PitchMethod.AMDF:
            return_type = [float]
        elif method is PitchMethod.ESPS:
            return_type = [(float,)]

        return Tcl.call(
            return_type,
            self,
            "pitch",
            "-method",
            method,
            *Tcl.to_tcl_args(
                end=self.end,
                framelength=frame_length,
                maxpitch=max,
                minpitch=min,
                start=self.start,
                windowlength=window_length,
            ),
        )


### AudioDevice ###
class _AudioDevice:
    _current_input = "default"
    _current_output = "default"
    _current_context_filter = None

    @property
    def supported_encodings(self) -> list[str]:
        return Tcl.call([str], "Snack::audio", "encodings")

    @property
    def supported_sample_rates(self) -> list[str]:
        return Tcl.call([int], "Snack::audio", "rates")

    @property
    def latency(self) -> float:
        return Tcl.call(float, "Snack::audio", "playLatency") / 1000

    @latency.setter
    def latency(self, new_latency: float) -> None:
        Tcl.call(None, "Snack::audio", "playLatency", new_latency * 1000)

    @property
    def inputs(self) -> list[str]:
        return Tcl.call([str], "Snack::audio", "inputDevices")

    @property
    def outputs(self) -> list[str]:
        return Tcl.call([str], "Snack::audio", "outputDevices")

    @property
    def default_input(self) -> str:
        return self._current_input

    @default_input.setter
    def default_input(self, device: str) -> str:
        self._current_input = device
        return Tcl.call(None, "Snack::audio", "selectInput", device)

    @property
    def default_output(self) -> str:
        return self._current_output

    @default_output.setter
    def default_output(self, device: str) -> str:
        self._current_output = device
        return Tcl.call(None, "Snack::audio", "selectOutput", device)

    @property
    def is_playing(self) -> bool:
        return Tcl.call(bool, "Snack::audio", "active")

    def resume_all(self) -> None:
        return Tcl.call(None, "Snack::audio", "play")

    def pause_all(self) -> None:
        return Tcl.call(None, "Snack::audio", "pause")

    def stop_all(self) -> None:
        return Tcl.call(None, "Snack::audio", "stop")


Device = _AudioDevice()
