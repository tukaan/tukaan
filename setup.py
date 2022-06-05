from setuptools import setup


def get_requirements():
    with open("requirements.txt", "r") as file:
        for line in [x.strip() for x in file]:
            if line and not line.startswith("#"):
                yield line


setup(
    name="tukaan",
    version="0.0.1.dev1",
    author="rdbende",
    author_email="rdbende@gmail.com",
    url="https://github.com/tukaan/tukaan",
    license="MIT license",
    python_requires=">=3.7",
    install_requires=list(get_requirements()),
    description="A modern, cross platform Python toolkit for creating desktop GUI applications, based on Tcl/Tk.",
    packages=[
        "tukaan",
        "tukaan/Serif",
        "tukaan/themes",
        "tukaan/tkdnd",
        "tukaan/widgets",
    ],
    package_data={
        "": [
            "Serif/pkg/*.*",
            "tkdnd/*/*.*",
        ]
    },
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
