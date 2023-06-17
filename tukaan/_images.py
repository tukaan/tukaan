from __future__ import annotations

import itertools
from dataclasses import dataclass

from PIL import Image as PillowImage
from PIL import _imagingtk  # type: ignore
from PIL import ImageSequence

from tukaan._base import TkWidget, Widget
from tukaan._collect import collector
from tukaan._properties import OptionDescriptor
from tukaan._tcl import Tcl


@dataclass
class ImageAnimator:
    name: str
    frames: itertools.cycle
    cmd: str | None = None

    def show_next(self):
        name, duration = next(self.frames)
        Tcl.eval(None, f"after {duration} {self.cmd};{self.name} copy {name} -compositingrule set")


def get_image_mode(image: PillowImage.Image) -> str:
    if hasattr(image, "apply_transparency"):
        image.apply_transparency()  # type: ignore

    try:
        mode = image.palette.mode
    except AttributeError:
        mode = "RGB"
    else:
        if mode not in {"1", "L", "RGB", "RGBA"}:
            mode = PillowImage.getmodebase(mode)

    return mode


def create_image(image: PillowImage.Image, transparent: bool = False) -> tuple[str, int]:
    if transparent:
        image = image.convert("RGBA")

    image.load()
    block = im = image.im

    if not im.isblock():
        mode = get_image_mode(image) if image.mode == "P" else image.mode
        block = im.new_block(mode, image.size)
        im.convert2(block, im)

    name: str = Tcl.eval(str, "image create photo")
    Tcl.eval(None, f"PyImagingPhoto {name} {block.id}")

    return name, int(image.info.get("duration", 50))


def create_animated_image(image: PillowImage.Image, transparent: bool = False) -> str:
    name = Tcl.eval(str, "image create photo")  # Image onto which individual frames will be copied
    frames = itertools.cycle(create_image(f, transparent) for f in ImageSequence.Iterator(image))

    animator = ImageAnimator(name, frames)
    animator.cmd = cmd = Tcl.to(animator.show_next)

    Tcl.call(None, "after", "idle", cmd)

    return name


def convert_pillow_to_tk(image: PillowImage.Image) -> str:
    if image in getattr(collector, "pil_images", {}).values():
        # TODO: document this behavior
        # >>> img = Image.load("spam.png")
        # >>> a = Image(.., image=Image.load("spam.png"))
        # >>> b = Image(.., image=img)
        # >>> a.image is b.image
        # True
        # >>> b.image is img
        # False
        # >>> b.image == img
        # True
        for k, v in collector.pil_images.items():  # type: ignore
            if v == image:
                return k

    transparent = "transparency" in image.info

    if getattr(image, "is_animated", False):
        image_name = create_animated_image(image, transparent)
    else:
        image_name, _ = create_image(image, transparent)

    collector.add("pil_images", image, name=image_name)
    return image_name


setattr(PillowImage.Image, "__to_tcl__", convert_pillow_to_tk)
setattr(PillowImage.Image, "__from_tcl__", lambda value: collector.get_by_key("pil_images", value))


class ImageProp(OptionDescriptor[PillowImage.Image, PillowImage.Image]):
    def __init__(self) -> None:
        super().__init__("image", PillowImage.Image)


class Image(Widget, widget_cmd="ttk::label", tk_class="TLabel"):
    image = ImageProp()

    def __init__(self, parent: TkWidget, image: PillowImage.Image | None = None) -> None:
        super().__init__(parent, image=image)
