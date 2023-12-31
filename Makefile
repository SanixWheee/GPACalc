.PHONY: format docker

format_python:
	py -m pip install -U black isort && black . && isort . --profile black

format_html:
	npm install -g prettier && prettier --write "**/*.html"

