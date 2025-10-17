.PHONY: check
check:
	uv sync --group test --group static
	uv run ruff format .
	uv run ruff check . --fix
	uv run pytest
	uv run mypy

.PHONY: unit
unit:
	uv sync --group test
	uv run pytest --cov=sqlfmt --cov-report term-missing --cov-report xml:tests/.coverage/cov.xml tests/unit_tests

.PHONY: lint
lint:
	uv sync --group static
	ruff format .
	ruff check . --fix
	mypy

.PHONY: profiling
profiling: .profiling/all.rstats
	uv sync --group dev
	uv run snakeviz ./.profiling/all.rstats

.PHONY: profiling_gitlab
profiling_gitlab: .profiling/gitlab.rstats
	uv sync --group dev
	uv run snakeviz ./.profiling/gitlab.rstats

.PHONY: profiling_rittman
profiling_rittman: .profiling/rittman.rstats
	uv sync --group dev
	uv run snakeviz ./.profiling/rittman.rstats

.profiling/all.rstats: $(wildcard src/**/*)
	uv run python -m cProfile -o ./.profiling/all.rstats -m sqlfmt_primer --single-process
.profiling/gitlab.rstats: $(wildcard src/**/*)
	uv run python -m cProfile -o ./.profiling/gitlab.rstats -m sqlfmt_primer gitlab --single-process
.profiling/rittman.rstats: $(wildcard src/**/*)
	uv run python -m cProfile -o ./.profiling/rittman.rstats -m sqlfmt_primer rittman --single-process
