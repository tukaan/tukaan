PYTHON_FILES := $(shell git ls-files | grep -E "\.py")

venv: env/touchfile

env/touchfile: requirements.txt requirements-dev.txt
	test -d env || python3 -m venv env
	. env/bin/activate; pip install -Ur requirements.txt
	. env/bin/activate; pip install -Ur requirements-dev.txt
	touch env/touchfile

init: venv
	. env/bin/activate; python3 -m pip install -e .

format: venv
	. env/bin/activate; python3 -m black $(PYTHON_FILES)
	. env/bin/activate; python3 -m isort $(PYTHON_FILES)

typecheck: venv
	. env/bin/activate; python3 -m pyright $(PYTHON_FILES)

test: venv
	. env/bin/activate; python3 -m pytest

clean:
	rm -rf env
	find -iname "*.pyc" -delete
