from setuptools import setup


def get_requirements():
    with open("requirements.txt", "r") as file:
        for line in [x.strip() for x in file]:
            if line and not line.startswith("#"):
                yield line


setup(
    name="tukaan",
    version="0.0.1.dev0",
    author="rdbende",
    author_email="rdbende@gmail.com",
    url="https://github.com/tukaan/tukaan",
    license="MIT license",
    python_requires=">=3.7",
    install_requires=list(get_requirements()),
    packages=[
        "tukaan",
        "tukaan/Serif",
        "tukaan/Snack",
        "tukaan/audio",
        "tukaan/themes",
        "tukaan/tkdnd",
        "tukaan/widgets",
    ],
    package_data={
        "": [
            "Snack/pkg/*.tcl",
            "Snack/pkg/*/*.*",
            "Serif/pkg/*.*",
            "tkdnd/*/*.*",
        ]
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
