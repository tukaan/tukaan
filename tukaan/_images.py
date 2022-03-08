from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import Image as PIL_Image  # type: ignore

from ._base import BaseWidget, CgetAndConfigure
from ._misc import HEX
from ._utils import _images, _pil_images, counts, create_command, get_tcl_interp, py_to_tcl_args
from .exceptions import TclError


class _image_converter_class:
    def __init__(self, image):
        if image in tuple(_pil_images.values()):
            # Tk gets full with photoimages (or idk why?), and makes them grayscale
            # this is a solution when a PIL image is used multiple times
            for key, value in tuple(_pil_images.items()):
                if value is image:
                    self._name = key
                    return

        try:
            _animated = image.is_animated
        except AttributeError:
            _animated = False

        self._transparent = False
        if "transparency" in image.info:
            self._transparent = True

        self.current_frame = 0
        self._image = image
        self._name = f"tukaan_image_{next(counts['images'])}"

        self._tcl_call = get_tcl_interp()._tcl_call
        self._tcl_eval = get_tcl_interp()._tcl_eval

        self._tcl_call(None, "image", "create", "photo", self._name)

        _images[self._name] = self  # gc
        _pil_images[self._name] = image

        try:
            from PIL import _imagingtk

            _imagingtk.tkinit(get_tcl_interp().tcl_interp_address, 1)
        except (ImportError, AttributeError, TclError) as e:
            raise e

        if _animated:
            self.image_frames = []
            self.show_frames_command = create_command(self.show_frame)
            self.start_animation()
        else:
            if self._transparent:
                self._image = self._image.convert("RGBA")

            self.create_tcl_image(self._name, self._image)

    def create_tcl_image(self, name: str, image: PIL_Image.Image) -> None:
        if not hasattr(image, "mode") and not hasattr(image, "size"):
            return

        if self._transparent:
            image = image.convert("RGBA")
        
        mode = image.mode
        image.load()

        try:
            duration = image.info["duration"]
        except KeyError:
            duration = 50
        
        if mode == "P":
            try:
                mode = image.palette.mode
                if mode not in {"1", "L", "RGB", "RGBA"}:
                    mode = PIL_Image.getmodebase(mode)
            except AttributeError:
                mode = "RGB"

        size = image.size
        image = image.im

        if image.isblock():
            block = image
        else:
            block = image.new_block(mode, size)
            image.convert2(block, image)

        self._tcl_eval(None, f"image create photo {name}\nPyImagingPhoto {name} {block.id}")

        return name, duration

    def start_animation(self) -> None:
        frame_count = 0
        try:
            while True:
                self._image.seek(frame_count)
                name = f"{self._name}_frame_{frame_count}"
                self.image_frames.append(self.create_tcl_image(name, self._image))
                frame_count += 1
        except EOFError:
            pass

        self.show_frame()

    def show_frame(self) -> None:
        frame_data = self.image_frames[self.current_frame]

        self.current_frame += 1
        if self.current_frame == len(self.image_frames):
            self.current_frame = 0

        self._tcl_eval(
            None,
            f"{self._name} copy {frame_data[0]} -compositingrule set"
            "\n"
            f"after {int(frame_data[1])} {self.show_frames_command}",
        )

    def to_tcl(self) -> str:
        return self._name

    @classmethod
    def from_tcl(cls, value: str) -> PIL_Image.Image:
        if isinstance(value, tuple):
            value = value[0]  # Sometimes tk.call returns a tuple for some reason
        return _pil_images.get(value, None)


def pil_image_to_tcl(self):
    return _image_converter_class(self).to_tcl()


PIL_Image.Image.to_tcl = pil_image_to_tcl


class Image(BaseWidget):
    _keys = {"image": _image_converter_class}
    _tcl_class = "ttk::label"

    def __init__(self, parent=None, image=None):
        BaseWidget.__init__(self, parent, image=image)


class Icon(CgetAndConfigure):
    _keys = {"data": str, "file": Path}

    def __init__(self, file: Optional[str | Path] = None, data: Optional[str] = None):
        self._tcl_call = get_tcl_interp()._tcl_call  # for CgetAndConfigure

        self._name = f"tukaan_icon_{next(counts['icons'])}"
        _images[self._name] = self

        self._tcl_call(
            None,
            "image",
            "create",
            "photo",
            self._name,
            *py_to_tcl_args(file=file, data=data),
        )

    def to_tcl(self):
        return self._name

    @classmethod
    def from_tcl(cls, value):
        return _images[value]


class IconFactory:
    def __init__(self, light_theme: str, dark_theme: str):
        self._light_icons_dir = dark_theme
        self._dark_icons_dir = light_theme
        self._current_dir = dark_theme
        self.cache: dict[str, Icon] = {}

        get_tcl_interp()._tcl_call(None, "bind", ".app", "<<ThemeChanged>>", self.change_theme)

    def change_theme(self):
        # fmt: off
        dark_theme = sum(
            HEX.from_hex(get_tcl_interp()._tcl_call(str, "ttk::style", "lookup", "TLabel.label", "-foreground")
        )) / 3 > 127
        # fmt: on

        self._current_dir = self._light_icons_dir if dark_theme else self._dark_icons_dir

        for icon_name, icon in tuple(self.cache.items()):
            icon.config(file=Path(self._current_dir) / (icon_name + ".png"))

    def __getitem__(self, icon_name: str) -> Icon:
        if icon_name in self.cache:
            return self.cache[icon_name]

        icon = Icon(file=Path(self._current_dir) / (icon_name + ".png"))
        self.cache[icon_name] = icon
        return icon

    get = __getitem__
