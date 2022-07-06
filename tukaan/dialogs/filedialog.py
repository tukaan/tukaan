from __future__ import annotations

import shutil
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import PIPE, run
from threading import Thread
from typing import IO

from tukaan._base import WindowBase
from tukaan._tcl import Tcl


def _get_path_from_command(args) -> Path | None:
    # FIXME: this function is a crazy hack
    result = None

    Tcl.call(None, "set", "waitforresult", "0")

    def wait_for_result():
        nonlocal result
        result = run(args, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout
        Tcl.call(None, "set", "waitforresult", "1")

    Thread(target=wait_for_result).start()
    Tcl.call(None, "tkwait", "variable", "waitforresult")

    if result:
        lines = result.splitlines()
        if len(lines) > 2:
            return [Path(item) for item in lines if item != "\n"]  # type: ignore
        return Path(lines[0])


class FileDialogBase(ABC):
    @staticmethod
    @abstractmethod
    def get_save_filename(*args, **kwargs) -> Path | None:
        pass

    @staticmethod
    @abstractmethod
    def get_open_filename(*args, **kwargs) -> Path:
        pass

    @staticmethod
    @abstractmethod
    def get_directory(*args, **kwargs) -> Path:
        pass

    @classmethod
    def get_open_file(
        cls,
        title: str | None = "Open file",
        *,
        directory: Path | None = None,
        filename: str | None = None,
        parent: WindowBase | None = None,
        mode: str = "r",
    ) -> IO | None:
        result = cls.get_open_filename(
            directory=directory,
            filename=filename,
            parent=parent,
            title=title,
        )
        if result:
            return result.open(mode)

    @classmethod
    def get_save_file(
        cls,
        title: str | None = "Save as",
        *,
        directory: Path | None = None,
        filename: str | None = None,
        parent: WindowBase | None = None,
        mode: str = "w",
        confirm: bool = True,
    ) -> IO | None:
        result = cls.get_save_filename(
            confirm=confirm,
            directory=directory,
            filename=filename,
            parent=parent,
            title=title,
        )
        if result:
            return result.open(mode)


class TkFileDialog(FileDialogBase):
    @staticmethod
    def get_save_filename(
        title: str | None = "Save as",
        *,
        directory: Path | None = None,
        filename: str | None = None,
        confirm: bool = True,
        parent: WindowBase | None = None,
    ) -> Path | None:
        result = Tcl.call(
            str,
            "tk_getSaveFile",
            *Tcl.to_tcl_args(
                confirmoverwrite=confirm,
                initialdir=directory,
                initialfile=filename,
                title=title,
                parent=parent,
            ),
        )
        if result:
            return Path(result)

    @staticmethod
    def get_open_filename(
        title: str | None = "Open file",
        *,
        directory: Path | None = None,
        filename: str | None = None,
        parent: WindowBase | None = None,
        multiple: bool = False,
    ) -> Path | list[Path] | None:
        return_type = [str] if multiple else str

        result = Tcl.call(
            return_type,
            "tk_getOpenFile",
            *Tcl.to_tcl_args(
                title=title,
                initialdir=directory,
                initialfile=filename,
                parent=parent,
                multiple=multiple,
            ),
        )

        if result:
            if not isinstance(result, list):
                return Path(result)
            if len(result) > 2:
                return [Path(item) for item in result if item != "\n"]  # type: ignore
            else:
                return Path(result[0])

    @staticmethod
    def get_directory(
        title: str | None = "Select directory",
        *,
        default: Path | None = None,
        parent: WindowBase | None = None,
    ) -> Path | None:
        result = Tcl.call(
            str,
            "tk_chooseDirectory",
            *Tcl.to_tcl_args(title=title, initialdir=default, parent=parent),
        )
        if result:
            return Path(result)


class ZenityFileDialog(FileDialogBase):
    @staticmethod
    def get_save_filename(
        title: str | None = "Save as",
        *,
        directory: Path | None = None,
        filename: str | None = None,
        confirm: bool = True,
        parent: WindowBase | None = None,
    ) -> Path | None:
        args = [
            "zenity",
            "--name=Tukaan",
            "--class=Tukaan",
            "--file-selection",
            "--save",
        ]

        if confirm:
            args.append("--confirm-overwrite")

        if filename:
            args.append(f"--filename={((directory or Path()) / filename).resolve()!s}")
        elif directory:
            args.append(f"--filename={directory.resolve()!s}")

        if title is not None:
            args.extend(["--title", title])

        id_ = parent.id if parent is not None else Tcl.call(str, "winfo", "id", ".")
        args.extend(["--modal", f"--attach={id_}"])

        return _get_path_from_command(args)

    @staticmethod
    def get_open_filename(
        title: str | None = "Open file",
        *,
        directory: Path | None = None,
        filename: str | None = None,
        parent: WindowBase | None = None,
        multiple: bool = False,
    ) -> Path | None:
        args = ["zenity", "--file-selection"]

        if filename:
            args.append(f"--filename={((directory or Path()) / filename).resolve()!s}")
        elif directory:
            stred = str(directory.resolve())
            if stred[-1] != "/":
                stred += "/"
            args.append(f"--filename={stred}")

        if multiple:
            args.extend(["--multiple", "--separator=\n"])

        if title is not None:
            args.extend(["--title", title])

        id_ = parent.id if parent is not None else Tcl.call(str, "winfo", "id", ".")
        args.extend(["--modal", f"--attach={id_}"])

        return _get_path_from_command(args)

    @staticmethod
    def get_directory(
        title: str | None = "Select directory",
        *,
        default: Path | None = None,
        parent: WindowBase | None = None,
    ) -> Path | None:
        args = ["zenity", "--file-selection", "--directory"]

        if default:
            args.append(f"--filename={default.resolve()!s}")

        if title is not None:
            args.extend(["--title", title])

        id_ = parent.id if parent is not None else Tcl.call(str, "winfo", "id", ".")
        args.extend(["--modal", f"--attach={id_}"])

        return _get_path_from_command(args)


class KDialogFileDialog(FileDialogBase):
    @staticmethod
    def get_save_filename(
        title: str | None = "Save as",
        *,
        directory: Path | None = None,
        filename: str | None = None,
        confirm: bool = True,
        parent: WindowBase | None = None,
    ) -> Path | None:
        args = ["kdialog", "--getsavefilename"]

        if filename:
            directory = (directory or Path()) / filename

        if directory:
            args.append(str(directory.resolve()))

        if title is not None:
            args.extend(["--title", title])

        id_ = str(parent.id) if parent is not None else Tcl.call(str, "winfo", "id", ".")
        args.extend(["--attach", id_])

        return _get_path_from_command(args)

    @staticmethod
    def get_open_filename(
        title: str | None = "Open file",
        *,
        directory: Path | None = None,
        filename: str | None = None,
        multiple: bool = False,
        parent: WindowBase | None = None,
    ) -> Path | None:
        args = ["kdialog", "--getopenfilename"]

        if filename:
            directory = (directory or Path()) / filename

        if directory:
            args.append(str(directory.resolve()))

        if multiple:
            args.extend(["--multiple", "--separate-output"])

        if title is not None:
            args.extend(["--title", title])

        id_ = str(parent.id) if parent is not None else Tcl.call(str, "winfo", "id", ".")
        args.extend(["--attach", id_])

        return _get_path_from_command(args)

    @staticmethod
    def get_directory(
        title: str | None = "Select directory",
        *,
        default: Path | None = None,
        parent: WindowBase | None = None,
    ) -> Path | None:
        args = ["kdialog", "--getexistingdirectory"]

        if default:
            args.append(str(default.resolve()))

        if title is not None:
            args.extend(["--title", title])

        id_ = str(parent.id) if parent is not None else Tcl.call(str, "winfo", "id", ".")
        args.extend(["--attach", id_])

        return _get_path_from_command(args)


if sys.platform != "linux":
    FileDialog = TkFileDialog
elif shutil.which("kdialog"):
    FileDialog = KDialogFileDialog
elif shutil.which("zenity"):
    FileDialog = ZenityFileDialog
