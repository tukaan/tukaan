from __future__ import annotations

from pathlib import Path

from PIL import Image as PIL_Image  # type: ignore

from ._tcl import Tcl
from ._utils import _images, _pil_images, counts
from .exceptions import TclError
from .widgets._base import BaseWidget, ConfigMixin


class PIL_TclConverter:
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

        Tcl.call(None, "image", "create", "photo", self._name)

        _images[self._name] = self  # gc
        _pil_images[self._name] = image

        try:
            from PIL import _imagingtk

            _imagingtk.tkinit(Tcl.interp_address, 1)
        except (ImportError, AttributeError, TclError) as e:
            raise e

        if _animated:
            self.image_frames = []
            self.show_frames_command = Tcl.create_cmd(self.show_frame)
            self.start_animation()
        else:
            if self._transparent:
                self._image = self._image.convert("RGBA")

            self.create_tcl_image(self._name, self._image)

    def create_tcl_image(self, name: str, image: PIL_Image.Image) -> tuple[str, int]:
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

        Tcl.eval(None, f"image create photo {name}\nPyImagingPhoto {name} {block.id}")

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

        Tcl.eval(
            None,
            f"{self._name} copy {frame_data[0]} -compositingrule set"
            "\n"
            f"after {int(frame_data[1])} {self.show_frames_command}",
        )

    def __to_tcl__(self) -> str:
        return self._name

    @classmethod
    def __from_tcl__(cls, value: str) -> PIL_Image.Image:
        if isinstance(value, tuple):
            value = value[0]  # Sometimes tk.call returns a tuple for some reason
        return _pil_images.get(value, None)


def pil_image_to_tcl(self):
    return PIL_TclConverter(self).__to_tcl__()


PIL_Image.Image.__to_tcl__ = pil_image_to_tcl


class Image(BaseWidget):
    _keys = {"image": PIL_TclConverter}
    _tcl_class = "ttk::label"

    def __init__(self, parent=None, image=None):
        BaseWidget.__init__(self, parent, image=image)


class Icon(ConfigMixin):
    _keys = {"data": str, "file": Path}

    def __init__(self, file: str | Path | None = None, data: str | None = None) -> None:
        self._name = f"tukaan_icon_{next(counts['icons'])}"
        _images[self._name] = self

        Tcl.call(
            None,
            "image",
            "create",
            "photo",
            self._name,
            *Tcl.to_tcl_args(file=file, data=data),
        )

    def __to_tcl__(self) -> str:
        return self._name

    @classmethod
    def __from_tcl__(cls, value: str) -> Icon:
        return _images[value]


class IconFactory:
    def __init__(self, light_theme: str, dark_theme: str):
        self._light_icons_dir = dark_theme
        self._dark_icons_dir = light_theme
        self._current_dir = dark_theme
        self.cache: dict[str, Icon] = {}

        Tcl.call(None, "bind", ".app", "<<ThemeChanged>>", self.change_theme)

    def change_theme(self):
        # fmt: off
        dark_theme = sum(
            HEX.from_hex(Tcl.call(str, "ttk::style", "lookup", "TLabel.label", "-foreground")
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
