.PHONY: check
check:
	isort .
	black .
	flake8 .
	mypy .