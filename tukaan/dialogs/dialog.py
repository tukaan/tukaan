from __future__ import annotations

import atexit
import shutil
import subprocess
import sys

from tukaan._base import ToplevelBase
from tukaan._tcl import Tcl
from tukaan.exceptions import TukaanTclError


class Dialog:
    if sys.platform != "linux":
        _type = "native"
    elif shutil.which("kdialog"):
        _type = "kdialog"
    if shutil.which("zenity"):
        _type = "kdialog"
    else:
        _type = "tukaan"


def run_in_subprocess(args: list[str]) -> str:
    process = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )
    atexit.register(process.kill)

    while True:
        if process.poll() is not None:
            break

        try:
            Tcl.do_one_event()
        except TukaanTclError:
            process.kill()
            return ""

    return process.communicate()[0]


def run_zenity(type_: str, title: str | None, parent: ToplevelBase | None, *options):
    args = [
        "zenity",
        type_,
        "--name=Tukaan",
        "--class=Tukaan",
    ]

    if title is not None:
        args.extend(["--title", title])

    args.extend(
        [
            "--modal",
            f"--attach={str(parent.id) if parent is not None else str(Tcl.call(int, 'winfo', 'id', '.'))}",
        ]
    )
    args.extend(options)

    return run_in_subprocess(args).splitlines()


def run_kdialog(
    type_: str, title: str | None, parent: ToplevelBase | None, *options
) -> list[str] | None:
    args = ["kdialog", type_]

    args.extend(options)

    if title is not None:
        args.extend(["--title", title])

    id_ = str(parent.id) if parent is not None else str(Tcl.call(int, "winfo", "id", "."))
    args.extend(["--attach", id_])

    return run_in_subprocess(args).splitlines()
