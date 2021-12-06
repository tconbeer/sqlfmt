# sqlfmt

![PyPI](https://img.shields.io/pypi/v/shandy-sqlfmt)
[![Lint and Test](https://github.com/tconbeer/sqlfmt/actions/workflows/test.yml/badge.svg)](https://github.com/tconbeer/sqlfmt/actions/workflows/test.yml)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/shandy-sqlfmt)
![Runs on Windows](https://img.shields.io/badge/runs%20on-Windows-blue)
![Runs on MacOS](https://img.shields.io/badge/runs%20on-MacOS-blue)
![Runs on Linux](https://img.shields.io/badge/runs%20on-Linux-blue)


sqlfmt is an opinionated CLI tool that formats your dbt SQL files. It is similar in nature to black, gofmt, 
and rustfmt.

sqlfmt is not configurable, except for line length. It enforces a single style. sqlfmt maintains comments and some extra newlines, but largely ignores all indentation and line breaks in the input file.

sqlfmt is not a linter. It does not parse your code; it just tokenizes it and tracks a small subset of tokens that impact formatting. This lets us "do one thing and do it well:" sqlfmt is very fast, and easier to maintain and extend than linters that need a full SQL grammar.

sqlfmt is designed to work with SQL files that contain jinja tags and blocks. It formats the code that users look at, and therefore doesn't need to know anything about what happens after the templates are rendered.

For now, sqlfmt only works on `select` statements (which is all you need if you use sqlfmt with a dbt project). In the future, it will be extended to DDL statements, as well.

## Installation and Getting Started
You will need Python 3.7-3.10 installed. You should use pipx or install into a virtual environment (maybe as a dev-dependency in your project). If you do not know how to install python and use pipx and/or virtual environments, go read about that first.

### Install Using pipx (recommended)

```
pipx install shandy-sqlfmt
```

### Other Installation Options
You should use a virutal environment to isolate sqlfmt's dependencies from others on your system. We recommend poetry (`poetry add -D shandy-sqlfmt`), or pipenv (`pipenv install -d shandy-sqlfmt`), but a simple `pip install shandy-sqlfmt` will also work.

### Other prerequisits
**sqlfmt is an alpha product** and will not always produce the formatted output you might want. It might even break your SQL syntax. It is **highly recommended** to only run sqlfmt on files in a version control system (like git), so that it is easy for you to revert any changes made by sqlfmt. On your first run, be sure to make a commit before running sqlfmt.

### Using sqlfmt
sqlfmt is a command-line tool. It works on any posix terminal and on Windows Powershell. If you have used `black`, the sqlfmt commands will look familiar. 

To list commands and options:

```bash
> sqlfmt --help
```

If you want to format all `.sql` and `.sql.jinja` files in your current working directory (and all nested directories), simply type:
```bash
> sqlfmt .
```
You can also supply a path to a one or more files or directories as arguments:
```bash
> sqlfmt /path/to/my/dir /path/to/a/file.sql
```
If you don't want to format the files you have on disk, you can run sqlfmt with the `--check` option. sqlfmt will exit with code 1 if the files on disk are not properly formatted:
```bash
> sqlfmt --check .
> sqlfmt --check path/to/my/dir
```
If you want to print a diff of changes that sqlfmt would make to format a file (but not update the file on disk), you can use the `--diff` option. `--diff` also exits with 1 on changes:
```bash
> sqlfmt --diff .
```

If you would like sqlfmt to ignore a file, or part of a file, you can add `-- fmt: off` and `-- fmt: on` comments to your code (or `# fmt: off` on MySQL or BigQuery). sqlfmt will not change any code between those comments; a single `-- fmt: off` at the top of a file will keep the entire file intact.

## The sqlfmt style
The only thing you can configure with sqlfmt is the desired line length of the formatted file. You can do this with the `--line-length` or `-l` options. The default is 88.

Given the desired line length, sqlfmt has four objectives:
1. Break and indent lines to make the syntactical structure of the code apparent
2. Break lines so they are shorter than the desired line length, if possible
3. Combine lines to use the least possible vertical space, without violating #1 and #2
4. Standardize capitalization (to lowercase) and in-line whitespace

sqlfmt borrows elements from well-accepted styles from other programming languages. It places opening brackets on the same line as preceding function names (like *black* for python and *1TBS* for C). It indents closing brackets to the same depth as the opening bracket (this is extended to statements that must be closed, like `case` and `end`).

The sqlfmt style is as simple as possible, with little-to-no special-casing of formatting concerns. While at first blush, this may not create a format that is as "nice" or "expressive" as hand-crafted indentation, over time, as you grow accustomed to the style, the consistency will allow you to jump between files, projects, and even companies much faster.

### Why lowercase?
There are several reasons that sqlfmt insists on lowercase SQL keywords:
1. We believe that SQL is code (this is a surprisingly controversial statement!). Shouting-case keywords perpetuate the myth that SQL isn't "real code", or isn't "modern" and somehow is trapped in the era of low-level imperative languages: BASIC, COBOL, and FORTRAN. The reality is that SQL is an incredibly powerful, declarative, and modern language. It should look like one.
1. Syntax highlighting for SQL makes shouting-case keywords redundant; the syntax highlighter in any text editor is going to be more consistent than any manual shout-casing. If you have a SQL query as a string inside of a block of code in another language, you may want to capitalize your keywords; sqlfmt only operates on dedicated SQL (and templated sql) files, so this is not relevant. However, even without syntax highlighting, the hierarchical and consistent indentation provided by sqlfmt provides sufficient visual structure without shout-casing keywords
1. Even among people who like shout-cased keywords, there are disagreements between what gets shout-cased. SELECT, sure, but SUM? AS? OVER? AND? All-lowercase keywords eliminates this potential source of irregularity and disagreement.
1. Research shows that generally, lowercase words are more readable

### Why trailing commas?
1. Using trailing commas follows the convention of every other written language and programming language
1. Leading commas require placing the first field name on the same line as `select`, which can obscure that field
1. SQL query compilation is extremely fast; the "cost" of "last field" errors is very low
1. trailing commas generalize better within `select` statements (e.g. `group by` and `partition by` clauses) and in other kinds of SQL statements (e.g. `insert` statements)

### Examples

sqlfmt will put very short queries on a single line:

```sql
SELECT a,
b,
   c
FROM my_table
```
becomes
```sql
select a, b, c from my_table
```

If a query doesn't fit on a single line, sqlfmt will format the query to make its hierarchy apparent. The main keywords in a `SELECT` statement are the top nodes in hierarchy. Individual fields are indented a single level; unless all fields fit on the same line as `select`, they must all be individually split onto their own lines. This is properly formatted code:
```sql
with t as (select * from my_schema."my_QUOTED_ table!")
select
    a_long_field_name,
    another_long_field_name,
    (one_field + another_field) as c,
    a_final_field
from t
where one_field < another_field
```

This hierarchical indentation scales to arbitrarily complex and nested queries. Another example of properly formatted code (at line length of 88):

```sql
select
    a,
    sum(a) over () as b,
    row_number() over () as c,
    count(case when a is null then 1 end) over (
        partition by user_id, date_trunc('year', performed_at)
    ) as d,
    first_value(a ignore nulls) over (
        partition by user_id
        order by performed_at desc
        rows between unbounded preceding and unbounded following
    ) as e
from my_table
```
Want more examples? See the `tests/data` directory, or go to http://sqlfmt.com to see how sqlfmt will format your queries.

## Contributing
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

### Setting up Your Dev Environment and Running Tests

1. Install [Poetry](https://python-poetry.org/docs/#installation) if you don't have it already. You may also need or want pyenv, make, and gcc. A complete setup from a fresh install of Ubuntu can be found [here](https://github.com/tconbeer/linux_setup)
1. Clone this repo into a directory (let's call it `sqlfmt`), then `cd sqlfmt`
1. Use `poetry install` to install the project (editable) and its dependencies into a new virtual env. To run `sqlfmt_primer`, you will need to install it (and its dependencies) by specifying it as an extra: `poetry install -E sqlfmt_primer`
1. Use `poetry shell` to spawn a subshell
1. Type `make` to run all tests and linters, or run `pytest`, `black`, `flake8`, `isort`, and `mypy` individually.

Note: If encountering a JSONDecodeError during `poetry install`, you will want to clear the poetry cache with `poetry cache clear pypi --all`.