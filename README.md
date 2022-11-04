# sqlfmt

[![PyPI](https://img.shields.io/pypi/v/shandy-sqlfmt)](https://pypi.org/project/shandy-sqlfmt/)
[![Downloads](https://static.pepy.tech/personalized-badge/shandy-sqlfmt?period=month&units=international_system&left_color=grey&right_color=orange&left_text=downloads/mo)](https://pepy.tech/project/shandy-sqlfmt)
[![Test](https://github.com/tconbeer/sqlfmt/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/tconbeer/sqlfmt/actions/workflows/test.yml)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/shandy-sqlfmt)
![Runs on Linux | MacOS | Windows](https://img.shields.io/badge/runs%20on-Linux%20%7C%20MacOS%20%7C%20Windows-blue)


sqlfmt formats your dbt SQL files so you don't have to. It is similar in nature to black, gofmt, 
and rustfmt (but for SQL). 

1. **sqlfmt promotes collaboration.** An auto-formatter makes it easier to collaborate with your team and solicit contributions from new people. You will never have to mention (or argue about) code style in code reviews again.
2. **sqlfmt is fast.** Forget about formatting your code, and spend your time on business logic instead. sqlfmt processes hundreds of files per second and only operates on files that have changed since the last run.
3. **sqlfmt works with Jinja.** It formats the code that users look at, and therefore doesn't need to know anything about what happens after the templates are rendered.
3. **sqlfmt integrates with your workflow.** As a CLI written in Python, it's easy to install locally on any OS and run in CI. Plays well with dbt, pre-commit, SQLFluff, VSCode, and GitHub Actions. sqlfmt powers the dbt Cloud IDE's Format button.

sqlfmt is not configurable, except for line length. It enforces a single style. sqlfmt maintains comments and some extra newlines, but largely ignores all indentation and line breaks in the input file.

sqlfmt is not a linter. It does not parse your code into an AST; it just lexes it and tracks a small subset of tokens that impact formatting. This lets us "do one thing and do it well:" sqlfmt is very fast, and easier to maintain and extend than linters that need a full SQL grammar.

For now, sqlfmt only works on `select`, `delete`, `grant`, `revoke`, and `create function` statements (which is all you need if you use sqlfmt with a dbt project). It is being extended to additional DDL and DML. Visit [this tracking issue](https://github.com/tconbeer/sqlfmt/issues/262) for more information.

## Documentation

Please visit [docs.sqlfmt.com](https://docs.sqlfmt.com) for more information on Getting Started, Integrations, the sqlfmt Style, and an API Reference. Or keep reading for an excerpt from the full docs.

### Installation

#### Try it first
Want to test out sqlfmt on a query before you install it? Go to [sqlfmt.com](https://sqlfmt.com) to use the interactive, web-based version.

#### Install Using pipx (recommended)
sqlfmt is a pip-installable Python package listed on PyPI under the name `shandy-sqlfmt`. You should install it into a virtual environment, which `pipx` does automatically:

```
pipx install shandy-sqlfmt
```

To install with the jinjafmt extra (which will also install the Python code formatter, *black*):

```
pipx install shandy-sqlfmt[jinjafmt]
```

For more installation options, [read the docs](https://docs.sqlfmt.com/getting-started/installation).

### Getting Started

#### Other prerequisites
**sqlfmt is an alpha product** and will not always produce the formatted output you might want. It might even break your SQL syntax. It is **highly recommended** to only run sqlfmt on files in a version control system (like git), so that it is easy for you to revert any changes made by sqlfmt. On your first run, be sure to make a commit before running sqlfmt.

#### Using sqlfmt
To list commands and options:

```bash
sqlfmt --help
```

If you want to format all `.sql` and `.sql.jinja` files in your current working directory (and all nested directories), simply type:
```bash
$ sqlfmt .
```

If you don't want to format the files you have on disk, you can run sqlfmt with the `--check` option. sqlfmt will exit with code 1 if the files on disk are not properly formatted:
```bash
$ sqlfmt --check .
```
If you want to print a diff of changes that sqlfmt would make to format a file (but not update the file on disk), you can use the `--diff` option. `--diff` also exits with 1 on changes:
```bash
$ sqlfmt --diff .
```

For more commands, see [the docs](https://docs.sqlfmt.com/getting-started/using-sqlfmt).

#### Configuring sqlfmt using pyproject.toml

Any command-line option for sqlfmt can also be set in a `pyproject.toml` file, under a `[tool.sqlfmt]` section header. Options passed at the command line will override the settings in the config file. [See the docs](https://docs.sqlfmt.com/getting-started/configuring-sqlfmt) for more information.

#### The jinjafmt extra

sqlfmt loves properly-formatted jinja, too.

[See the docs](https://docs.sqlfmt.com/getting-started/formatting-jinja) for more information about using the `jinjafmt` extra or disabling jinja formatting.

### Using sqlfmt with different SQL dialects

sqlfmt's rules are simple, which means it does not have to parse every single token in your query. This allows nearly all SQL dialects to be formatted using sqlfmt's default "polyglot" dialect, which requires no configuration.

The exception to this is [ClickHouse](https://docs.sqlfmt.com/dialects/#clickhouse), which is case-sensitive where other dialects are not. To prevent the lowercasing of function names, database identifiers, and aliases, use the `--dialect clickhouse` option when running sqlfmt. For example,

```bash
$ sqlfmt . --dialect clickhouse
```

This can also be configured using the `pyproject.toml` file:

```toml
[tool.sqlfmt]
dialect = "clickhouse"
```

Note that with this option, sqlfmt will not lowercase **most** non-reserved keywords, even common ones like `sum` or `count`. See (and please join) [this discussion](https://github.com/tconbeer/sqlfmt/discussions/229) for more on this topic.

### Integrations

sqlfmt plays nicely with other analytics engineering tools. For more information, [see the docs](https://docs.sqlfmt.com/category/integrations).

#### dbt

sqlfmt was built for dbt, so only [minimal configuration](https://docs.sqlfmt.com/integrations/dbt) is required. We recommend excluding your `target` and `dbt_packages` directories from formatting. You can do this with the command-line `--exclude` option, or by setting `exclude` in your `pyproject.toml` file:

```toml
[tool.sqlfmt]
exclude=["target/**/*", "dbt_packages/**/*"]
```

#### Other Integrations

Config for other integrations is detailed in the docs linked below:

- [pre-commit](https://docs.sqlfmt.com/integrations/pre-commit)
- [SQLFluff](https://docs.sqlfmt.com/integrations/sqlfluff)
- [VSCode](https://docs.sqlfmt.com/integrations/vs-code)


## The sqlfmt style
The only thing you can configure with sqlfmt is the desired line length of the formatted file. You can do this with the `--line-length` or `-l` options. The default is 88.

sqlfmt borrows elements from well-accepted styles from other programming languages. It places opening brackets on the same line as preceding function names (like *black* for python and *1TBS* for C). It indents closing brackets to the same depth as the opening bracket (this is extended to statements that must be closed, like `case` and `end`).

The sqlfmt style is as simple as possible, with little-to-no special-casing of formatting concerns. While at first blush, this may not create a format that is as "nice" or "expressive" as hand-crafted indentation, over time, as you grow accustomed to the style, formatting becomes transparent and the consistency will allow you to jump between files, projects, and even companies much faster.

[Read More](https://docs.sqlfmt.com/style/)

### Why lowercase?
Because SQL is code! But there are [other good reasons too](https://docs.sqlfmt.com/style/#why-lowercase).

### Why trailing commas?
Using trailing commas follows the convention of every other written language and programming language. [But wait, there's more.](https://docs.sqlfmt.com/style/#why-trailing-commas)

## Contributing

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Maintainability](https://api.codeclimate.com/v1/badges/8928f6662a67b8eaf092/maintainability)](https://codeclimate.com/github/tconbeer/sqlfmt/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/8928f6662a67b8eaf092/test_coverage)](https://codeclimate.com/github/tconbeer/sqlfmt/test_coverage)

### Providing Feedback

We'd love to hear from you! [Open an Issue](https://github.com/tconbeer/sqlfmt/issues/new/choose) to request new features, report bad formatting, or say hello.

### Setting up Your Dev Environment and Running Tests

1. Install [Poetry](https://python-poetry.org/docs/#installation) v1.2 or higher if you don't have it already. You may also need or want pyenv, make, and gcc. A complete setup from a fresh install of Ubuntu can be found [here](https://github.com/tconbeer/linux_setup).
1. Clone this repo into a directory (let's call it `sqlfmt`), then `cd sqlfmt`.
1. Use `poetry install --all-extras --sync` to install the project (editable) and its dependencies (including the `jinjafmt` and `sqlfmt_primer` extras) into a new virtual env.
1. Use `poetry shell` to spawn a subshell.
1. Type `make` to run all tests and linters, or run `pytest`, `black`, `flake8`, `isort`, and `mypy` individually.

### Updating primer repos to reflect formatting changes

1. Make sure all changes are committed to sqlfmt.
1. Check out `main` in the repo and make sure you `pull` changes locally.
1. Check out the `unformatted` tag in the repo with `git checkout -b chore/apply-abc123 unformatted` where `abc123` is the hash of the most recent sqlfmt commit (from 1).
1. Run sqlfmt against the working tree, then `git add .` and `git commit -m "chore: apply sqlfmt abc123"`.
1. We will have conflicts with main that we want to ignore, so merge main into this branch, ignoring anything on main: `git merge -s ours main`.
1. Push and open a PR; squash and merge. Grab the commit SHA.
1. Paste the commit SHA as a ref into `primer.py`.
1. Run `sqlfmt_primer -k` to clear the cache, then update the stats in `primer.py` to match the results.
