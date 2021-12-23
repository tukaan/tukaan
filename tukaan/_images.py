from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from PIL import Image as PIL_Image

from ._base import BaseWidget
from ._utils import (
    _icons,
    _images,
    counts,
    create_command,
    get_tcl_interp,
    py_to_tcl_arguments,
)
from .exceptions import TclError


class _image_converter_class:
    def __init__(self, image):
        try:
            self.is_animated = image.is_animated
        except AttributeError:
            self.is_animated = False

        self.current_frame = 0
        self._image = image

        self._name = f"tukaan_image_{next(counts['image'])}"
        get_tcl_interp()._tcl_call(None, "image", "create", "photo", self._name)
        _images[self._name] = self

        try:
            from PIL import _imagingtk

            _imagingtk.tkinit(get_tcl_interp().tcl_interp_address, 1)
        except (ImportError, AttributeError, TclError) as e:
            raise e

        if self.is_animated:
            self.image_frames = []
            self.show_frames_command = create_command(self.show_frame)
            self.start_animation()
        else:
            threading.Thread(target=self.create_tcl_image, args=(self._image,)).start()

    def get_image_mode(self, image):
        # currently this is a copy/pasta from PIL.ImageTk
        if hasattr(image, "mode") and hasattr(image, "size"):
            mode = image.mode
            if mode == "P":
                image.load()
                try:
                    mode = image.palette.mode
                except AttributeError:
                    mode = "RGB"
        else:
            mode = image
            image = None

        if mode not in {"1", "L", "RGB", "RGBA"}:
            mode = PIL_Image.getmodebase(mode)

        return mode, image

    def create_tcl_image(self, image, frame: int | None = None):
        name = self._name
        if frame is not None:
            name = f"{self._name}_frame_{frame}"

        get_tcl_interp()._tcl_call(None, "image", "create", "photo", name)

        self._mode, image = self.get_image_mode(image)
        image.load()

        size = image.size
        mode = image.mode

        image = image.im

        if image.isblock() and mode == self._mode:
            block = image
        else:
            block = image.new_block(self._mode, size)
            image.convert2(block, image)

        get_tcl_interp()._tcl_call(None, "PyImagingPhoto", name, block.id)

        return name

    def start_animation(self):
        frame_count = 0
        try:
            while True:
                self._image.seek(frame_count)
                frame = self.create_tcl_image(self._image, frame=frame_count)

                try:
                    delay = self._image.info["duration"]
                except:
                    delay = 100

                self.image_frames.append((frame, delay))
                frame_count += 1
        except EOFError:
            pass

        self.show_frame()

    def show_frame(self):
        frame_data = self.image_frames[self.current_frame]

        get_tcl_interp()._tcl_call(
            None, self._name, "copy", frame_data[0], "-compositingrule", "set"
        )

        self.current_frame += 1
        if self.current_frame == len(self.image_frames):
            self.current_frame = 0

        get_tcl_interp()._tcl_call(
            None, "after", int(frame_data[1]), self.show_frames_command
        )

    def to_tcl(self):
        return self._name

    @classmethod
    def from_tcl(cls, value):
        return _images[value]


class Image(BaseWidget):
    _keys = {"image": _image_converter_class}
    _tcl_class = "ttk::label"

    def __init__(self, parent=None, image=None):
        if isinstance(image, PIL_Image.Image):
            image = _image_converter_class(image)
        BaseWidget.__init__(self, parent, image=image)

    def config(self, **kwargs):
        image = kwargs.pop("image", None)
        if image:
            if isinstance(image, PIL_Image.Image):
                image = _image_converter_class(image)
            BaseWidget.config(self, image=image)


class Icon:
    def __init__(self, file: Optional[str | Path] = None, data: Optional[str] = None):
        self._name = f"tukaan_icon_{next(counts['icons'])}"
        _icons[self._name] = self

        get_tcl_interp()._tcl_call(
            None,
            "image",
            "create",
            "photo",
            self._name,
            *py_to_tcl_arguments(file=file, data=data),
        )

    def to_tcl(self):
        return self._name

    @classmethod
    def from_tcl(cls, value):
        return _icons[value]
