PYTHON_FILES := $(shell git ls-files | grep -E "\.py")

init:
	python3 -m venv env
	sh env/bin/activate
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install:
	sh env/bin/activate
	pip install -e .

format:
	python3 -m black $(PYTHON_FILES)
	python3 -m isort $(PYTHON_FILES)

test:
	sh env/bin/activate
	python3 -m pytest
