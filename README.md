# Tukaan

Tukaan is the new, pythonic and colorful (like a keel-billed toucan) framework that aims to replace Tkinter.
It has everything (on my computer, not at GitHub) that you need to develop cross-platform GUIs.


## WIP
Although all the basic widgets and other classes already exist in my local repo, they are not yet ready to push them to GitHub.
I only push things to GitHub that work and can be tried, but they are still in progress, so you shouldn’t use it in any project.


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
	def __init__(self, title="My nice little Tukaan app"):
		tukaan.App.__init__(self, title=title)

		self.position = "center"

		self.button = tukaan.Button(self, text="Button", command=lambda: print("ok"))

		self.pack_widgets()
	
	def pack_widgets(self):
		self.button.pack()


def main():
	app = MyApp()

	app.run()


if __name__ == "__main__":
	main() 
```


## Credits
Many thing in Tukaan is based on:

- [Akuli's Teek](https://github.com/Akuli/teek) (TODO: which, and why?)
- [Ckyiu's TkZero](https://github.com/UnsignedArduino/TkZero)
- one of my private Gists
