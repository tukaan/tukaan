from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from tukaan._base import ToplevelBase
from tukaan._tcl import Tcl

from .dialog import Dialog, run_kdialog, run_zenity


class FileDialogBase(ABC):
    @staticmethod
    @abstractmethod
    def pick_path_to_open(*args, **kwargs) -> Path | list[Path] | None:
        pass

    @staticmethod
    @abstractmethod
    def pick_path_to_save(*args, **kwargs) -> Path | None:
        pass

    @staticmethod
    @abstractmethod
    def pick_directory(*args, **kwargs) -> Path | None:
        pass


class TkFileDialog(FileDialogBase):
    @staticmethod
    def pick_path_to_open(
        title: str | None = None,
        *,
        directory: Path | None = None,
        filename: str | None = None,
        parent: ToplevelBase | None = None,
        multiple: bool = False,
        filetypes: dict[str, str | tuple[str, ...]] = None,
    ) -> Path | list[Path] | None:
        return_type = [str] if multiple else str

        if filetypes is not None:
            filetypes_processed = tuple((name, filter_) for name, filter_ in filetypes.items())
        else:
            filetypes_processed = None

        if directory is not None and not isinstance(directory, Path):
            raise TypeError("directory must be a pathlib.Path object")

        result = Tcl.call(
            return_type,
            "tk_getOpenFile",
            *Tcl.to_tcl_args(
                title=title,
                initialdir=directory,
                initialfile=filename,
                parent=parent,
                multiple=multiple,
                filetypes=filetypes_processed,
            ),
        )

        if result:
            if not isinstance(result, list):
                return Path(result)
            elif len(result) == 1:
                return Path(result[0])
            else:
                return [Path(x) for x in result if x != "\n"]  # type: ignore

    @staticmethod
    def pick_path_to_save(
        title: str | None = None,
        *,
        directory: Path | None = None,
        filename: str | None = None,
        confirm: bool = True,
        parent: ToplevelBase | None = None,
        filetypes: dict[str, str | tuple[str, ...]] = None,
    ) -> Path | None:

        if filetypes is not None:
            filetypes_processed = tuple((name, filter_) for name, filter_ in filetypes.items())
        else:
            filetypes_processed = None

        if directory is not None and not isinstance(directory, Path):
            raise TypeError("directory must be a pathlib.Path object")

        result = Tcl.call(
            str,
            "tk_getSaveFile",
            *Tcl.to_tcl_args(
                confirmoverwrite=confirm,
                initialdir=directory,
                initialfile=filename,
                title=title,
                parent=parent,
                filetypes=filetypes_processed,
            ),
        )

        if result:
            return Path(result)

    @staticmethod
    def pick_directory(
        title: str | None = None,
        *,
        default: Path | None = None,
        parent: ToplevelBase | None = None,
    ) -> Path | None:
        if default is not None and not isinstance(default, Path):
            raise TypeError("default directory must be a pathlib.Path object")

        result = Tcl.call(
            str,
            "tk_chooseDirectory",
            *Tcl.to_tcl_args(title=title, initialdir=default, parent=parent),
        )

        if result:
            return Path(result)


class TukaanFileDialog(FileDialogBase):
    ...


class ZenityFileDialog(FileDialogBase):
    @staticmethod
    def pick_path_to_open(
        title: str | None = None,
        *,
        directory: Path | None = None,
        filename: str | None = None,
        parent: ToplevelBase | None = None,
        multiple: bool = False,
        filetypes: dict[str, str | tuple[str, ...]] = None,
    ) -> Path | None:
        args = []

        if directory is not None and not isinstance(directory, Path):
            raise TypeError("directory must be a pathlib.Path object")

        if filename:
            args.append(f"--filename={((directory or Path()) / filename).resolve()!s}")
        elif directory:
            stred = str(directory.resolve())
            if stred[-1] != "/":
                stred += "/"
            args.append(f"--filename={stred}")

        if multiple:
            args.extend(["--multiple", "--separator=\n"])

        if filetypes:
            for name, filter_ in filetypes.items():
                if isinstance(filter_, tuple):
                    filter_ = " ".join(filter_)
                args.append(f"--file-filter={name}|{filter_}")

        result = run_zenity("--file-selection", title, parent, *args)

        if result:
            if len(result) == 1:
                return Path(result[0])
            else:
                return [Path(x) for x in result]

    @staticmethod
    def pick_path_to_save(
        title: str | None = None,
        *,
        directory: Path | None = None,
        filename: str | None = None,
        confirm: bool = True,
        parent: ToplevelBase | None = None,
        filetypes: dict[str, str | tuple[str, ...]] = None,
    ) -> Path | None:
        args = ["--save"]

        if directory is not None and not isinstance(directory, Path):
            raise TypeError("directory must be a pathlib.Path object")

        if confirm:
            args.append("--confirm-overwrite")

        if filename:
            args.append(f"--filename={((directory or Path()) / filename).resolve()!s}")
        elif directory:
            args.append(f"--filename={directory.resolve()!s}")

        if filetypes:
            for name, filter_ in filetypes.items():
                if isinstance(filter_, tuple):
                    filter_ = " ".join(filter_)
                args.append(f"--file-filter={name}|{filter_}")

        result = run_zenity("--file-selection", title, parent, *args)

        if result:
            return Path(result[0])

    @staticmethod
    def pick_directory(
        title: str | None = None,
        *,
        default: Path | None = None,
        parent: ToplevelBase | None = None,
    ) -> Path | None:
        args = ["--directory"]

        if default is not None and not isinstance(default, Path):
            raise TypeError("default directory must be a pathlib.Path object")

        if default:
            args.append(f"--filename={default.resolve()!s}")

        result = run_zenity("--file-selection", title, parent, *args)

        if result:
            return Path(result[0])


class KFileDialog(FileDialogBase):
    @staticmethod
    def pick_path_to_open(
        title: str | None = None,
        *,
        directory: Path | None = None,
        filename: str | None = None,
        multiple: bool = False,
        parent: ToplevelBase | None = None,
        filetypes: dict[str, str | tuple[str, ...]] = None,
    ) -> Path | None:
        args = []

        if directory is not None and not isinstance(directory, Path):
            raise TypeError("directory must be a pathlib.Path object")

        if filename:
            directory = (directory or Path()) / filename

        if directory:
            args.append(str(directory.resolve()))

        if multiple:
            args.extend(["--multiple", "--separate-output"])

        result = run_kdialog("--getopenfilename", title, parent, *args)

        if result:
            if len(result) == 1:
                return Path(result[0])
            else:
                return [Path(x) for x in result]

    @staticmethod
    def pick_path_to_save(
        title: str | None = None,
        *,
        directory: Path | None = None,
        filename: str | None = None,
        confirm: bool = True,
        parent: ToplevelBase | None = None,
        filetypes: dict[str, str | tuple[str, ...]] = None,
    ) -> Path | None:
        args = []

        if directory is not None and not isinstance(directory, Path):
            raise TypeError("directory must be a pathlib.Path object")

        if filename:
            directory = (directory or Path()) / filename

        if directory:
            args.append(str(directory.resolve()))

        result = run_kdialog("--getsavefilename", title, parent, *args)

        if result:
            return Path(result[0])

    @staticmethod
    def pick_directory(
        title: str | None = None,
        *,
        default: Path | None = None,
        parent: ToplevelBase | None = None,
    ) -> Path | None:
        args = []

        if default is not None and not isinstance(default, Path):
            raise TypeError("default directory must be a pathlib.Path object")

        if default:
            args.append(str(default.resolve()))

        result = run_kdialog("--getexistingdirectory", title, parent, *args)

        if result:
            return Path(result[0])


DISPATCHER = {
    "kdialog": KFileDialog,
    "native": TkFileDialog,
    "tukaan": TukaanFileDialog,
    "zenity": ZenityFileDialog,
}


class FileDialog(Dialog):
    @classmethod
    def pick_path_to_open(cls, *args, **kwargs):
        return DISPATCHER[cls._type].pick_path_to_open(*args, **kwargs)

    @classmethod
    def pick_path_to_save(cls, *args, **kwargs):
        return DISPATCHER[cls._type].pick_path_to_save(*args, **kwargs)

    @classmethod
    def pick_directory(cls, *args, **kwargs):
        return DISPATCHER[cls._type].pick_directory(*args, **kwargs)
