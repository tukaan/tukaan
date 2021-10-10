# Tukaan

[![Code style: black](https://img.shields.io/badge/code%20style-black-1c1c1c.svg)](https://github.com/psf/black)

Tukaan is the new pythonic, powerful and easy-to-use GUI framework that aims to replace Tkinter.
It has everything (at least on my computer) that you need to develop cross-platform GUIs.


## WIP
Although all the basic widgets and other classes already exist in my local repo, they are not yet ready to push them to GitHub.
I only push things to GitHub that work and could be used, but they are still in progress, so you shouldn’t use it in any project.


## The goal of Tukaan
The goal of Tukaan is to be an easy-to-use, powerful and pythonic alternative to Tkinter.

Tkinter is just a wrapper around Tk, that is so thin, that you can see through it, and even has holes on it. If you have ever used Tkinter, you know, it's kinda dumb. There are a lot of things not implemented in Tkinter, you can only access them with Tcl calls. Tukaan has everything you could need, and maybe even more.

In Tcl almost everything is represented as strings, and Tkinter doesn't convert them to Python objects, so you have to do that yourself. If you mess something up, it won't raise a Python exception, but Tcl a error, which you don't know what's wrong even if you know the Tcl language.
Tkinter also looks awful by default. You can change this, if you use the the Ttk extensions. But why should you use extensions to make your GUI not look like it came from the 90's?

With Tukaan this is completely different. With it, the app looks native by default on Windows and on Mac OS as well. Unfortunately this isn't possible on Linux, but it uses a better theme than the Tk default.


## Simple example

```python
import tukaan

class MyApp(tukaan.App):
    def __init__(self):
        tukaan.App.__init__(self, title="My nice little Tukaan app")

        self.position = "center"

        self.button = tukaan.Button(self, text="Button")
        self.button.callback = lambda: print("ok")
        self.button.layout.grid(row=0, column=0, margin=(1, 2, 3, 4))


def main():
    MyApp().run()

if __name__ == "__main__":
    main() 
```

## Some very nice things in tukaan

### Lay out widgets in a griddy system
You can specify cells for the grid layout in a list of sublists to set rows, columns, rowspans, and columnspans for the widgets, making it super easy and apparent what the layout will look like. 
```python
import tukaan


class MyApp(tukaan.App):
    def __init__(self):
        tukaan.App.__init__(self)

        self.layout.grid_cells = [["button", "button"], ["label", "entry"]]

        self.button = tukaan.Button(self, text="Button")
        self.label = tukaan.Label(self, text="Label")
        self.entry = tukaan.Entry(self)

        self.button.layout.grid(cell="button", align="stretch")
        self.label.layout.grid(cell="label", align="stretch")
        self.entry.layout.grid(cell="entry", align="stretch")
        


def main():
    MyApp().run()


if __name__ == "__main__":
    main()
```
Extending widgets isn’t that hard, so you just need to template the rows or columns, and you need to set *stretchiness* on the widget.
```python
import tukaan


class MyApp(tukaan.App):
    def __init__(self):
        tukaan.App.__init__(self)

        self.layout.grid_col_template = (1, 0, 2)

        for col, (name, text) in enumerate(zip(
            ("button_1", "button_2", "button_3"),
            ("Button 1", "Button 2", "Button 3")
        )):
            setattr(self, name, tukaan.Button(self, text=text))
            getattr(self, name).layout.grid(row=0, col=col, align="stretch")


def main():
    MyApp().run()


if __name__ == "__main__":
    main()
```

You can easily set margins for your widgets ...\
*the same for every side*
```python
widget.layout.grid(cell="some_cell", margin=(2))
```
*different horizontal and vertical*
```python
widget.layout.grid(cell="some_cell", margin=(2, 10))
```
*2 on top, 10 on right, 6 on bottom and 10 on left*
```python
widget.layout.grid(cell="some_cell", margin=(2, 10, 6))
```
*2 on top, 10 on top, 6 on right, 4 on left*
```python
widget.layout.grid(cell="some_cell", margin=(2, 10, 6, 4))
```
... and you can simply modify any attributes
```python
widget.layout.cell = "other_cell"
```
```python
widget.layout.config(margin=0)
```

### Get clipboard content
TODO: currently not working with images
```python
print(tukaan.Clipboard.get())

# or

print(tukaan.Clipboard.content)
```

### When was the user last active on the computer
```python
print("User last active", tukaan.App().user_last_active, "seconds ago.")
```

### Centering a window on the screen
FIXME: For some reason it doesn't work sometimes

```python
app = tukaan.App()
app.position = "center"
```

### Color conversions
```python
color = tukaan.Color("#007fff")
print(color.rgb)
>>> (0, 127, 255)
print(color.hsv)
>>> (210, 100, 100)
print(color.cmyk)
>>> (100, 50, 0, 0)
```

### Screen information
```python
screen = tukaan.Screen()  # you don't need to instanciate it
print(screen.width)
>>> 1920
print(screen.height)
>>> 1080
print(screen.dpi)
>>> 72
```

### Cursor stuff
```python
cursor = tukaan.Cursor  # not instanciate it, just have a reference
print(cursor.x)
>>> 123
print(cursor.y)
>>> 456
cursor.x = 456  # cursor moved
print(cursor.position)
>>> (456, 456)
```



## Credits
- Logo design:

    Inspired by Tajulislam12's design: [`https://dribbble.com/shots/14487668-toucan-logo-design-Icon`](https://dribbble.com/shots/14487668-toucan-logo-design-Icon)

- Logo font:

    Stick No Bills by Mooniak: [`https://fonts.google.com/specimen/Stick+No+Bills`](https://fonts.google.com/specimen/Stick+No+Bills)

- Many thing in Tukaan is based on:

  - [Akuli's Teek](https://github.com/Akuli/teek) (TODO: which parts and why?)
  - [Ckyiu's TkZero](https://github.com/UnsignedArduino/TkZero)
  - one of my private Gists
