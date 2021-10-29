# sqlfmt

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

sqlfmt is an opinionated CLI tool that formats your dbt sql files. It is similar in nature to black, gofmt, 
and rustfmt.

sqlfmt is not configurable, except for line length. It enforces a single style. sqlfmt maintains comments and some extra newlines, but largely ignores all indentation and line breaks in the input file.

sqlfmt is not a linter. It does not parse your code; it just tokenizes it and tracks a small subset of tokens that impact formatting. This lets us "do one thing and do it well:" sqlfmt is very fast, and easier to extend than linters that need a full sql grammar.

sqlfmt is designed to work with sql files that contain jinja tags and blocks. It formats the code that users look at, and therefore doesn't need to know anything about what happens after the templates are rendered.

## Contributing

### Setting up Your Dev Environment and Running Tests

1. Install [Poetry](https://python-poetry.org/docs/#installation) if you don't have it already. You may also need or want pyenv, make, and gcc. A complete setup from a fresh install of Ubuntu can be found [here](https://github.com/tconbeer/linux_setup)
1. Clone this repo into a directory (let's call it `sqlfmt`), then `cd sqlfmt`
1. Use `poetry install` to install the project (editable) and its dependencies into a new virtual env
1. Use `poetry shell` to spawn a subshell
1. Type `make` to run all tests and linters, or run `pytest`, `black`, `flake8`, `isort`, and `mypy` individually.