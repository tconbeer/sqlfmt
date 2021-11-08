# sqlfmt

![PyPI](https://img.shields.io/pypi/v/shandy-sqlfmt)
[![Lint and Test](https://github.com/tconbeer/sqlfmt/actions/workflows/test.yml/badge.svg)](https://github.com/tconbeer/sqlfmt/actions/workflows/test.yml)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/shandy-sqlfmt)
![Runs on Windows](https://img.shields.io/badge/runs%20on-Windows-blue)
![Runs on MacOS](https://img.shields.io/badge/runs%20on-MacOS-blue)
![Runs on Linux](https://img.shields.io/badge/runs%20on-Linux-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)


sqlfmt is an opinionated CLI tool that formats your dbt sql files. It is similar in nature to black, gofmt, 
and rustfmt.

sqlfmt is not configurable, except for line length. It enforces a single style. sqlfmt maintains comments and some extra newlines, but largely ignores all indentation and line breaks in the input file.

sqlfmt is not a linter. It does not parse your code; it just tokenizes it and tracks a small subset of tokens that impact formatting. This lets us "do one thing and do it well:" sqlfmt is very fast, and easier to extend than linters that need a full sql grammar.

sqlfmt is designed to work with sql files that contain jinja tags and blocks. It formats the code that users look at, and therefore doesn't need to know anything about what happens after the templates are rendered.

## Installation and Getting Started
You will need Python 3.7-3.10 installed. sqlfmt has a dependency on [Click](https://click.palletsprojects.com/en/8.0.x/), so you should use `pipx` or install into a virtual environment (maybe as a dev-dependency in your project).

### Install Using pipx (recommended)

```
pipx install shandy-sqlfmt
```

### Other Installation Options
You should use a virutal environment to isolate sqlfmt's dependencies from others on your system. We recommend poetry (`poetry add -D shandy-sqlfmt`), or pipenv (`pipenv install -d shandy-sqlfmt`), but a simple `pip install shandy-sqlfmt` will also work.

### Other prerequisits
**sqlfmt is an alpha product** and will not always produce the formatted output you might want. It might even break your sql syntax. It is **highly recommended** to only run sqlfmt on files in a version control system (like git), so that it is easy for you to revert any changes made by sqlfmt. On your first run, be sure to make a commit before running sqlfmt.

### Using sqlfmt
sqlfmt is a command-line tool. It works on any posix terminal and on Windows Powershell. If you have used `black`, the sqlfmt commands will look familiar. To list commands and options:

```
sqlfmt --help
```

From your current working directory, `sqlfmt .` will format all files `.sql` or `.sql.jinja` files in your working directory or any nested directories. You can also supply a path to a single file or a directory as an argument `sqlfmt /path/to/my/dir`. Using the `--check` or `--diff` options, like `sqlfmt --check` will prevent sqlfmt from writing formatted files, and the program will exit with an exit code of 1 if it detects any changes.

## Contributing

### Setting up Your Dev Environment and Running Tests

1. Install [Poetry](https://python-poetry.org/docs/#installation) if you don't have it already. You may also need or want pyenv, make, and gcc. A complete setup from a fresh install of Ubuntu can be found [here](https://github.com/tconbeer/linux_setup)
1. Clone this repo into a directory (let's call it `sqlfmt`), then `cd sqlfmt`
1. Use `poetry install` to install the project (editable) and its dependencies into a new virtual env
1. Use `poetry shell` to spawn a subshell
1. Type `make` to run all tests and linters, or run `pytest`, `black`, `flake8`, `isort`, and `mypy` individually.