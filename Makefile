.PHONY: check
test:
	pytest
	isort .
	black .
	flake8 .
	mypy .