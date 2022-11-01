from __future__ import annotations

import subprocess
from pathlib import Path

from tukaan._tcl import Tcl
from tukaan.colors import Color, rgb

from .lookandfeel import LookAndFeel
from .themes import Theme

plasma_colors_map = {
    "view_bg": ("Colors:View", "BackgroundNormal"),
    "button_bg": ("Colors:Button", "BackgroundNormal"),
    "button_hover_bg": ("Colors:Button", "DecorationHover"),
    "button_fg": ("Colors:Button", "ForegroundNormal"),
    "button_hover_fg": ("Colors:Selection", "ForegroundNormal"),
    "select_bg": ("Colors:Selection", "BackgroundNormal"),
    "select_fg": ("Colors:Selection", "ForegroundNormal"),
    "tooltip_bg": ("Colors:Tooltip", "BackgroundNormal"),
    "tooltip_fg": ("Colors:Tooltip", "ForegroundNormal"),
    "tooltip_border": ("Colors:Tooltip", "BackgroundAlternate"),
    "focus_color": ("Colors:Button", "DecorationFocus"),
}


class KolorScheme(Theme):
    is_native = True

    @classmethod
    def use(cls) -> None:
        if not LookAndFeel._kreadconfig_available:
            Tcl.call(None, "ttk::style", "theme", "use", "clam")
            return

        if not cls._inited:
            theme_script = (Path(__file__).parent / "kolorscheme.tcl").read_text()
            Tcl.eval(None, theme_script.format(**cls._get_colors()))

            cls._inited = True

        Tcl.call(None, "ttk::style", "theme", "use", "clam")
        Tcl.call(None, "::ttk::theme::clam::configure_colors")

    @staticmethod
    def _get_colors() -> dict:
        rgb_colors = {}

        for color, (group, key) in plasma_colors_map.items():
            rgb_colors[color] = tuple(
                map(
                    int,
                    subprocess.Popen(
                        ["kreadconfig5", "--group", group, "--key", key],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    .stdout.read()
                    .decode()
                    .split(",")[:3],
                )
            )

        for name, color in rgb_colors.items():
            rgb_colors[name] = rgb(*color)

        rgb_colors["disabled_fg"] = (
            Color(rgb_colors["button_fg"]).mix(Color(rgb_colors["view_bg"]), 1 / 1).hex
        )

        return rgb_colors
