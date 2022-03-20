# Tukaan
[![Code style: black](https://img.shields.io/badge/code%20style-black-1c1c1c.svg)](https://github.com/psf/black)

Website: https://tukaan.github.io/docs/

## This is a work-in-progress project.
I don't release a package to Pypi, because I break backwards-compatibility alomost with every commit, and because I still have to write tests, to see, what works, and what doesn't. You can still use it by downloading or cloning the repo, but there's no `setup.py` to install it on the system.

## The goal of Tukaan
The goal of Tukaan is to be an **easy-to-use**, **powerful** and **Pythonic** GUI framework.

## Why not Tkinter?
Tkinter is just a wrapper around Tk, that is so thin, that you can see through it, and even has holes on it. If you have ever used Tkinter, you know, it's kinda dumb. There are a lot of things not implemented in Tkinter, that you can only access with Tcl calls. Tukaan has everything you could need, and maybe even more :)

In Tcl almost everything is represented as strings, and Tkinter doesn't always convert them to Python objects, so you have to do that yourself. If you mess something up, it won't raise a Python exception, but Tcl a error instead, which you don't understand, even if you know the Tcl language.

Tkinter also looks awful by default. You can change this, if you use the the Ttk extensions. But why should you use extensions to make your GUI not look like it came from the 90's?
With Tukaan this is completely different. The apps look native by default on Windows and on MacOS as well. Unfortunately this isn't possible on Linux, but it still uses a better theme than the Tk default.


## Credits
- Many thing in Tukaan is based on:
  - [Akuli's Teek](https://github.com/Akuli/teek)
- And there are some thing that are inspired by
  - [TkZero](https://github.com/UnsignedArduino/TkZero)
  - [GUIZero](https://github.com/lawsie/guizero)
- Logo design is inspired by [Tajulislam12's design on Dribbble](https://dribbble.com/shots/14487668-toucan-logo-design-Icon)
