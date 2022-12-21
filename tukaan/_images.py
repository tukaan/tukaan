from __future__ import annotations

import itertools
from pathlib import Path
from typing import Union

from PIL import Image as PillowImage
from PIL import ImageSequence
from PIL import _imagingtk as ImagingTk  # type: ignore

from tukaan._base import TkWidget, WidgetBase
from tukaan._collect import _images, counter
from tukaan._props import OptionDesc
from tukaan._tcl import Tcl
from tukaan.colors import Color


class Pillow2Tcl:
    def __init__(self, image: PillowImage.Image) -> None:
        self._name = f"tukaan_image_{next(counter['images'])}"
        self._pil_image = image

        _images[self._name] = self

        try:
            self._animated = image.is_animated
        except AttributeError:
            self._animated = False

        self._transparent = "transparency" in image.info

        if not self._animated:
            self._create(image, name=self._name)
        else:
            # Image into which individual frames will be copied
            Tcl.call(None, "image", "create", "photo", self._name)

            # Set up animation frames
            self._setup_animation(image)
            self._show_cmd = Tcl.to(self._show_next_frame)
            self._schedule_next_cmd = (
                f"after {{}} {self._show_cmd}\n{self._name} copy {{}} -compositingrule set"
            )
            Tcl.eval(None, f"after idle {self._show_cmd}")

    def _getmode(self, image: PillowImage.Image) -> str:
        """Get the mode of palette mapped data."""

        image.apply_transparency()
        try:
            mode = image.palette.mode
            if mode not in {"1", "L", "RGB", "RGBA"}:
                mode = PillowImage.getmodebase(mode)
        except AttributeError:
            mode = "RGB"

        return mode

    def _create(self, image: PillowImage.Image, name: str | None = None) -> tuple[int, str]:
        assert hasattr(image, "mode")
        assert hasattr(image, "size")

        if self._transparent:
            image = image.convert("RGBA")

        image.load()

        duration = int(image.info.get("duration", 50))
        size = image.size
        im = image.im

        if im.isblock():
            block = im
        else:
            mode = self._getmode(image) if image.mode == "P" else image.mode
            block = im.new_block(mode, size)
            im.convert2(block, im)

        name = Tcl.eval(str, f"image create photo {name or ''}")
        Tcl.eval(None, f"PyImagingPhoto {name} {block.id}")

        return duration, name

    def _setup_animation(self, image: PillowImage.Image) -> None:
        frames = []

        for frame in ImageSequence.Iterator(image):
            frames.append(self._create(frame))

        self._frames = itertools.cycle(frames)

    def _show_next_frame(self) -> None:
        Tcl.eval(None, self._schedule_next_cmd.format(*next(self._frames)))

    @staticmethod
    def dispose(image_name: str) -> None:
        image = _images.get(image_name)

        if image is None:
            return

        del _images[image_name]

        Tcl.eval(None, f"image delete {image._name}")

        if image._animated:
            Tcl.eval(None, f"after cancel {image._show_cmd}")

            frames = []
            for _, name in image._frames:
                if name in frames:
                    break
                frames.append(name)

            Tcl.call(None, "image", "delete", *frames)

    @classmethod
    def __from_tcl__(cls, value: str) -> PillowImage.Image | Icon | None:
        result = _images.get(value)

        if hasattr(result, "_pil_image"):
            return result._pil_image

        return result


def pil_image_to_tcl(self) -> str:
    return Pillow2Tcl(self)._name


PillowImage.Image.__to_tcl__ = pil_image_to_tcl


class Icon:
    def __init__(self, source: Path) -> None:
        self._name = f"tukaan_icon_{next(counter['icons'])}"
        _images[self._name] = self

        Tcl.call(None, "image", "create", "photo", self._name, "-file", source)

    @property
    def source(self) -> None:
        return Tcl.call(Path, self._name, "cget", "-file")

    @source.setter
    def source(self, source: Path) -> None:
        Tcl.call(None, self._name, "configure", "-file", source)

    @classmethod
    def __from_tcl__(cls, value: str) -> Icon | PillowImage.Image | None:
        return Pillow2Tcl.__from_tcl__(value)


class IconFactory:
    def __init__(self, on_light_theme: Path, on_dark_theme: Path | None) -> None:
        self.cache: dict[str, Icon] = {}

        self._dark_icons_dir = on_light_theme
        self._light_icons_dir = on_dark_theme

        self._current_dir = on_light_theme

        if on_dark_theme is not None:
            Tcl.call(None, "bind", ".app", "<<ThemeChanged>>", self._change_theme)

    def _change_theme(self) -> None:
        fg = Tcl.call(str, "ttk::style", "lookup", "TLabel.label", "-foreground")

        if Color(fg).is_dark:
            self._current_dir = self._dark_icons_dir
        else:
            self._current_dir = self._light_icons_dir

        assert self._current_dir is not None

        for name, icon in self.cache.items():
            icon.source = Path(self._current_dir) / f"{name}.png"

    def get(self, icon_name: str) -> Icon:
        if icon_name in self.cache:
            return self.cache[icon_name]

        icon = Icon(Path(self._current_dir) / f"{icon_name}.png")
        self.cache[icon_name] = icon

        return icon

    __getitem__ = get


class ImageProp(OptionDesc[Pillow2Tcl, Union[PillowImage.Image, Icon]]):
    def __init__(self) -> None:
        super().__init__("image", Pillow2Tcl)


class Image(WidgetBase):
    _tcl_class = "ttk::label"

    image = ImageProp()

    def __init__(
        self,
        parent: TkWidget,
        image: PillowImage.Image | None = None,
        *,
        tooltip: str | None = None,
    ) -> None:
        WidgetBase.__init__(self, parent, image=image, tooltip=tooltip)
