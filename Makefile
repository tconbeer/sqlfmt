.PHONY: check
check:
	ruff format .
	ruff check . --fix
	pytest
	mypy

.PHONY: unit
unit:
	pytest --cov=sqlfmt --cov-report term-missing --cov-report xml:tests/.coverage/cov.xml tests/unit_tests

.PHONY: lint
lint:
	ruff format .
	ruff check . --fix
	mypy

.PHONY: profiling
profiling: .profiling/all.rstats
	snakeviz ./.profiling/all.rstats

.PHONY: profiling_gitlab
profiling_gitlab: .profiling/gitlab.rstats
	snakeviz ./.profiling/gitlab.rstats

.PHONY: profiling_rittman
profiling_rittman: .profiling/rittman.rstats
	snakeviz ./.profiling/rittman.rstats

.profiling/all.rstats: $(wildcard src/**/*)
	python -m cProfile -o ./.profiling/all.rstats -m sqlfmt_primer --single-process
.profiling/gitlab.rstats: $(wildcard src/**/*)
	python -m cProfile -o ./.profiling/gitlab.rstats -m sqlfmt_primer gitlab --single-process
.profiling/rittman.rstats: $(wildcard src/**/*)
	python -m cProfile -o ./.profiling/rittman.rstats -m sqlfmt_primer rittman --single-process
