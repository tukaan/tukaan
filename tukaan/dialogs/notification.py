from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tukaan.app import App


class Notification:
    @staticmethod
    def send(
        title: str,
        message: str | None = None,
        *,
        icon: str | Path | None = None,  # TODO: Support tukaan.Icon
    ) -> None:
        if shutil.which("notify-send"):
            if message is None:
                message = ""

            args = ["notify-send", title, message, "-a", App.shared_instance.name]

            if icon:
                if isinstance(icon, Path):
                    icon = str(icon.resolve())

                args.extend(["-i", icon])

            subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
