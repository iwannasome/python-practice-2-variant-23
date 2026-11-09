PYTHON = .venv/bin/python

.PHONY: test lint mbt-file mbt-tiny build

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m pycodestyle src tests
	.venv/bin/ruff check src tests
	.venv/bin/ruff format --check src tests
	.venv/bin/flake8 src tests
	$(PYTHON) tests/audit_project.py

mbt-file:
	$(PYTHON) -m coverage run --branch --data-file=.coverage.file -m pytest tests/test_mbt_file.py -q
	$(PYTHON) -m coverage report --data-file=.coverage.file
	$(PYTHON) -m coverage json --data-file=.coverage.file -o coverage-file.json
	$(PYTHON) -m coverage html --data-file=.coverage.file -d htmlcov-file
	$(PYTHON) tests/check_mbt_coverage.py coverage-file.json

mbt-tiny:
	$(PYTHON) -m coverage run --branch --data-file=.coverage.tiny -m pytest tests/test_mbt_tiny.py -q
	$(PYTHON) -m coverage report --data-file=.coverage.tiny
	$(PYTHON) -m coverage json --data-file=.coverage.tiny -o coverage-tiny.json
	$(PYTHON) -m coverage html --data-file=.coverage.tiny -d htmlcov-tiny
	$(PYTHON) tests/check_mbt_coverage.py coverage-tiny.json

build:
	$(PYTHON) -m build --wheel
