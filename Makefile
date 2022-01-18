.PHONY: check
check:
	pytest
	isort .
	black .
	flake8 .
	mypy

.PHONY: unit
unit:
	pytest --cov=sqlfmt --cov-report term-missing --cov-report xml:tests/.coverage/cov.xml tests/unit_tests

.PHONY: lint
lint:
	isort .
	black .
	flake8 .
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

.profiling/all.rstats: src
	python -m cProfile -o ./.profiling/all.rstats -m sqlfmt_primer
.profiling/gitlab.rstats: src
	python -m cProfile -o ./.profiling/gitlab.rstats -m sqlfmt_primer gitlab
.profiling/rittman.rstats: src
	python -m cProfile -o ./.profiling/rittman.rstats -m sqlfmt_primer rittman

