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
