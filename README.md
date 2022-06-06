<p align="center">
  <img src="https://raw.githubusercontent.com/tukaan/.github/master/assets/tukaan.png" alt="Tukaan" width="150px">
  <h1 align="center">Tukaan</h1>
</p>


[![tukaan.github.io](https://img.shields.io/badge/Website-tukaan.github.io-%23ec9f30)](https://tukaan.github.io)
[![#StandWithUkraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg)](https://www.standwithukraine.how/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-1c1c1c.svg)](https://github.com/psf/black)

#### Tukaan is a modern, cross platform Python toolkit for creating desktop GUI applications

## Install

You can use `pip` to install [Tukaan from Pypi](https://pypi.org/project/tukaan/)

On Linux or macOS:
```
pip3 install tukaan
```

or Windows:
```
pip install tukaan
```

On Linux you may get an error that the `_tkinter` module is not found. In that case you need to install the `python3-tk` package with your package manager.


## Why not Tkinter?
Tkinter is just a wrapper around Tk, that is so thin, that you can see through it, and even has holes on it. If you have ever used Tkinter, you know, it's kinda dumb. There are a lot of things not implemented in Tkinter, that you can only access with Tcl calls. Tukaan has everything you could need, and maybe even more :)

In Tcl almost everything is represented as strings, and Tkinter doesn't always convert them to Python objects, so you have to do that yourself. If you mess something up, it won't raise a Python exception, but Tcl a error instead, which you don't understand, even if you know the Tcl language.

Tkinter also looks awful by default. You can change this, if you use the the Ttk extensions. But why should you use extensions to make your GUI not look like it came from the 90's?
With Tukaan this is completely different. The apps look native by default on Windows and on MacOS as well. Unfortunately this isn't possible on Linux, but it still uses a better theme than the Tk default.


## Credits
- Many things in Tukaan are based on:
  - [Akuli's Teek](https://github.com/Akuli/teek)
- And there are some thing that are inspired by
  - [TkZero](https://github.com/UnsignedArduino/TkZero)
  - [GUIZero](https://github.com/lawsie/guizero)
- Logo design is inspired by [Tajulislam12's design on Dribbble](https://dribbble.com/shots/14487668-toucan-logo-design-Icon)
