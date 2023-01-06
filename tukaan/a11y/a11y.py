from __future__ import annotations

import shutil
from subprocess import PIPE, run

from tukaan._system import Platform
from tukaan._tcl import Tcl
from tukaan._utils import classproperty

plasma_reduced_motion_command = [
    "kreadconfig5",
    "--file",
    "kdeglobals",
    "--group",
    "KDE",
    "--key",
    "AnimationDurationFactor",
]


class Accessibility:
    @classmethod
    def allow_focus_follows_mouse(cls) -> None:
        Tcl.call(None, "tk_focusFollowsMouse")

    @classproperty
    def prefers_reduced_motion(cls) -> bool:
        if Platform.os == "Windows":
            from winreg import HKEY_CURRENT_USER, OpenKey, QueryValueEx

            key_name = r"Control Panel\Desktop\WindowMetrics"

            try:
                reg_key = OpenKey(HKEY_CURRENT_USER, key_name)
                value = QueryValueEx(reg_key, "MinAnimate")[0]
            except FileNotFoundError:
                return False
            else:
                return not int(value)
        elif shutil.which("kreadconfig5"):
            result = run(plasma_reduced_motion_command, stdout=PIPE, stderr=PIPE, check=True).stdout
            try:
                return result.decode().split()[0] == "0"
            except IndexError:
                return False
        return False
