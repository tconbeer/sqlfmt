# sqlfmt (personal fork)

This is a personal, private fork of [sqlfmt](https://github.com/tconbeer/sqlfmt), the SQL
formatter for dbt projects. It is not published to PyPI, not accepting outside contributions,
and not meant for use outside this project — it exists to format my own dbt models in a
specific house style that differs from upstream sqlfmt's defaults.

sqlfmt's formatting engine (lexer, CLI, Jinja handling, etc.) does the heavy lifting; this fork
layers a custom set of formatting rules on top. See `docs/spec-custom-style.md` for the house
style this fork targets.

sqlfmt is not a linter — it doesn't parse SQL into an AST, it lexes it and tracks a small set of
tokens relevant to formatting. It currently formats `select`, `delete`, `grant`, `revoke`, and
`create function` statements, which covers typical dbt model SQL.

## Using this fork

This fork is installed from source, not from PyPI:

```bash
git clone <this repo>
cd sqlfmt
uv sync --all-groups --all-extras
uv run sqlfmt .
```

Common commands:

```bash
sqlfmt .            # format all .sql and .sql.jinja files under the current directory
sqlfmt --check .     # exit 1 if any files aren't formatted; make no changes
sqlfmt --diff .      # print a diff of what would change
echo "select 1" | sqlfmt -   # format from stdin, write formatted SQL to stdout
```

**Before your first run on a project, commit your working tree.** sqlfmt may not always produce
the output you want, and on rare inputs it can even break SQL syntax, so make sure you can
revert.

### Configuring

Options can be set under `[tool.sqlfmt]` in `pyproject.toml`, e.g.:

```toml
[tool.sqlfmt]
line_length = 100
exclude = ["target/**/*", "dbt_packages/**/*"]
```

### Dialects

The default "polyglot" dialect works for most SQL. Use `--dialect clickhouse` (or
`dialect = "clickhouse"` in `pyproject.toml`) for ClickHouse's case-sensitive identifiers.

## Development

```bash
uv sync --all-groups --all-extras
make check   # ruff format/check, pytest, mypy
```

`make unit` runs just the unit tests with coverage.

## License

Apache-2.0, inherited from upstream sqlfmt. See `LICENSE`.
