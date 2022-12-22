import shutil
import sys
from pathlib import Path

from setuptools import setup

directory = Path(__file__).parent


def get_requirements():
    with (directory / "requirements.txt").open() as file:
        for line in [x.strip() for x in file]:
            if line and not line.startswith("#"):
                yield line


def get_long_description():
    with (directory / "README.md").open() as file:
        return file.read()


package_data = {
    "apt": {
        "cmd": ["apt", "install"],
        "_tkinter": "python3-tk",
        "imagetk": "python3-pil.imagetk",
    },
    "dnf": {
        "cmd": ["dnf", "install"],
        "_tkinter": "python3-tkinter",
        "imagetk": "python3-pillow-tk",
    },
    "pacman": {
        "cmd": ["pacman", "-S"],
        "_tkinter": "tk",
        "imagetk": "python-pillow",
    },
}


def prompt_install_linux(packages: [str]) -> None:
    for package_manager in ("apt", "pacman", "dnf"):
        if shutil.which(package_manager):
            system_package_manager = package_manager
            break

    stuff = package_data[system_package_manager]
    package_names = [stuff[name] for name in packages if stuff.get(name)]

    print(
        "The following packages must be installed in order to use Tukaan:",
        f"  {' '.join(package_names)}\n",
        f"Please install {'it' if len(package_names) == 1 else 'them'} "
        + "with the following command (root privileges may be required):",
        "  " + " ".join(stuff["cmd"] + package_names),
        sep="\n",
    )
    sys.exit(1)


def prompt_install_mac(packages: [str]) -> None:
    if "_tkinter" in packages:
        if float(_tkinter.TK_VERSION) < 8.6:
            print(
                "Tcl/Tk for Python is not installed on your system.",
                "Please install Python with Tcl/Tk included.",
                sep="\n",
            )
        else:
            print(
                f"Your Tcl/Tk version is too old ({_tkinter.TK_VERSION}).",
                "Please install a newer version of Tcl/Tk for Python on your system.",
                sep="\n",
            )
        sys.exit(1)


def prompt_install_windows(packages: [str]) -> None:
    if "_tkinter" in packages:
        print(
            "Tcl/Tk for Python is not installed on your system.",
            "Please modify your Python installation and make sure that the "
            + '"tcl/tk and IDLE" option is turned on in the Optional features page.',
            sep="\n",
        )
        sys.exit(1)


to_be_installed = []

try:
    import _tkinter
except ImportError:
    to_be_installed.append("_tkinter")
else:
    if float(_tkinter.TK_VERSION) < 8.6:
        to_be_installed.append("_tkinter")

try:
    from PIL import ImageTk
except ImportError:
    to_be_installed.append("imagetk")

if to_be_installed:
    {
        "win32": prompt_install_windows,
        "linux": prompt_install_linux,
        "darwin": prompt_install_mac,
    }.get(sys.platform, lambda *_: ...)(to_be_installed)


setup(
    name="tukaan",
    version="0.2.0",
    license="MIT license",
    author="rdbende",
    author_email="rdbende@gmail.com",
    url="https://tukaan.github.io",
    project_urls={
        "Documentation": "https://tukaan.github.io/docs",
        "Source": "https://github.com/tukaan/tukaan",
        "Tracker": "https://github.com/tukaan/tukaan/issues",
    },
    python_requires=">=3.7",
    install_requires=list(get_requirements()),
    description="A modern, cross platform Python toolkit for creating desktop GUI applications.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords=["gui", "tcl", "tcl/tk", "tk", "tkinter", "ttk", "tukaan", "ui"],
    packages=[
        "tukaan",
        "tukaan/a11y",
        "tukaan/dialogs",
        "tukaan/fonts",
        "tukaan/theming",
        "tukaan/widgets",
        "tukaan/windows",
    ],
    include_package_data=True,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Tcl",
        "Programming Language :: C",
        "Programming Language :: C++",
        "Typing :: Typed",
    ],
)
