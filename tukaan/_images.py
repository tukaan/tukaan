from __future__ import annotations

import contextlib
from pathlib import Path

from PIL import Image as PIL_Image  # type: ignore

from ._base import WidgetBase
from ._props import cget, config
from ._tcl import Tcl
from ._utils import _images, _pil_images, counts
from .colors import Color

try:
    from PIL import Image as PillowImage
    from PIL import _imagingtk as ImagingTk  # type: ignore
except ImportError as e:
    raise ImportError("Tukaan needs PIL and PIL._imagingtk in order to display images.") from e

PHOTO_CMD = "image create photo {name}\nPyImagingPhoto {name} {blockid}"


class Pillow2Tcl:
    _cur_f = 0

    def __init__(self, image: PillowImage.Image):
        if image in _pil_images.values():
            for key, value in _pil_images.items():
                if value is image:
                    self._name = key
                    return

        try:
            _animated = image.is_animated
        except AttributeError:
            _animated = False

        self._transparent = "transparency" in image.info
        self._image = image
        self._name = f"tukaan_image_{next(counts['images'])}"

        Tcl.call(None, "image", "create", "photo", self._name)
        ImagingTk.tkinit(Tcl.interp_address, 1)

        _images[self._name] = self  # gc
        _pil_images[self._name] = image

        if _animated:
            self.frames = []
            self.show_cmd = Tcl.create_cmd(self._show)
            self._start()
        else:
            self._create(self._name, self._image)

    def _create(self, name: str, image: PillowImage.Image) -> tuple[str, int]:
        if not hasattr(image, "mode") and not hasattr(image, "size"):
            raise

        if self._transparent:
            image = image.convert("RGBA")

        mode = image.mode
        image.load()

        if mode == "P":
            try:
                mode = image.palette.mode
                if mode not in {"1", "L", "RGB", "RGBA"}:
                    mode = PillowImage.getmodebase(mode)
            except AttributeError:
                mode = "RGB"

        try:
            duration = int(image.info["duration"])
        except KeyError:
            duration = 50

        size = image.size
        im = image.im

        if im.isblock():
            block = im
        else:
            block = im.new_block(mode, size)
            im.convert2(block, im)

        Tcl.eval(None, PHOTO_CMD.format(name=name, blockid=block.id))

        return name, duration

    def _start(self) -> None:
        frame_count = 0
        with contextlib.suppress(EOFError):
            while True:
                name = f"{self._name}_frame_{frame_count}"
                self._image.seek(frame_count)
                self.frames.append(self._create(name, self._image))
                frame_count += 1

        self._len = frame_count - 1
        self._show()

    def _show(self) -> None:
        name, duration = self.frames[self._cur_f]

        if self._cur_f != self._len:
            self._cur_f += 1
        else:
            self._cur_f = 0

        Tcl.eval(
            None,
            f"{self._name} copy {name} -compositingrule set\n"
            + f"after {duration} {self.show_cmd}",
        )

    def __to_tcl__(self) -> str:
        return self._name

    @classmethod
    def __from_tcl__(cls, value: str) -> PIL_Image.Image | None:
        if isinstance(value, (tuple, list)):
            [value] = value
        return _pil_images.get(value)


def pil_image_to_tcl(self):
    return Pillow2Tcl(self).__to_tcl__()


setattr(PillowImage.Image, "__to_tcl__", pil_image_to_tcl)


class Icon:
    def __init__(self, file: str | Path | None = None) -> None:
        self._name = f"tukaan_icon_{next(counts['icons'])}"
        _images[self._name] = self

        Tcl.call(
            None,
            "image",
            "create",
            "photo",
            self._name,
            *Tcl.to_tcl_args(file=file),
        )

    def config(self, file: Path | None = None):
        Tcl.call(
            None,
            self._name,
            "configure",
            *Tcl.to_tcl_args(file=file),
        )

    def __to_tcl__(self) -> str:
        return self._name

    @classmethod
    def __from_tcl__(cls, value: str) -> Icon:
        return _images[value]  # type: ignore


class IconFactory:
    def __init__(self, on_light: Path, on_dark: Path | None):
        self._light_icons_dir = on_light
        self._dark_icons_dir = on_dark
        self._current_dir = on_light
        self.cache: dict[str, Icon] = {}

        self._current_dir = on_light

        if on_dark is not None:
            Tcl.call(None, "bind", ".app", "<<ThemeChanged>>", self.change_icon_theme)

    def change_icon_theme(self):
        is_dark = Color(
            Tcl.call(str, "ttk::style", "lookup", "TLabel.label", "-foreground")
        ).is_dark

        self._current_dir = self._light_icons_dir if is_dark else self._dark_icons_dir
        assert self._current_dir is not None

        for name, icon in self.cache.items():
            icon.config(file=Path(self._current_dir) / f"{name}.png")

    def get(self, icon_name: str) -> Icon:
        if icon_name in self.cache:
            return self.cache[icon_name]

        assert self._current_dir is not None
        icon = Icon(file=Path(self._current_dir) / f"{icon_name}.png")
        self.cache[icon_name] = icon
        return icon

    __getitem__ = get


def get_image(self) -> PillowImage.Image | Icon:
    return cget(self, Pillow2Tcl, "-image")


def set_image(self, value: PillowImage.Image | Icon) -> None:
    config(self, image=value)


image = property(get_image, set_image)


class Image(WidgetBase):
    _tcl_class = "ttk::label"

    image = image

    def __init__(self, parent, image: PillowImage.Image | None = None):
        WidgetBase.__init__(self, parent, image=image)
