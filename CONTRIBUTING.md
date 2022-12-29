# Developing Tukaan

I've tried to make contributing easy. I've compiled all kinds of tasks in [TODO.md](TODO.md), and you can pick whichever one you like. It doesn't matter what level you are at in Python, or if you know any Tcl/Tk at all, every contribution moves this project forward.

## Get started
To get started, make a fork of Tukaan to your account. Then run these commands below. You'll obviously need Python and [Git](https://git-scm.com/) to develop Tukaan, but if you're here you probably already have it.

```
git clone https://github.com/YourUserName/tukaan
```

then switch to the newly clone repo with `cd tukaan`

Create a virtual Python environment and activate it. On a Windows system you need tu use `py` instead of `python3`.

➡ On Windows:
```
py -m venv env
env\Scripts\activate
```

➡ On any other system:
```
python3 -m venv env
source env/bin/activate
```

Then install the requirements with `pip`:
```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Don't forget to re-activate the virtual environment after you closed the terminal, and re-opened it!

Now you can open Tukaan in your favorite IDE, and start developing!


## Tools we use
We use `black` and `isort` to format our code, and you should run them on the files you edit, although you don't have to do this every time you change something. Github actions tell us before I merge the pull request, so it doesn't really matter if you forget to run them.

If you installed the modules listed in `requirements-dev.txt` then you already have `black` and `isort`. If not, you can install them with `pip`. Your IDE might also have a plugin for these tools.
