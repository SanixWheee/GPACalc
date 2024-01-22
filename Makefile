.PHONY: format_python format_html

format_python:
	py -m pip install -U black isort && py -m black . -S && py -m isort . --profile black

format_html:
	npm install -g prettier && prettier --write "**/*.html"

