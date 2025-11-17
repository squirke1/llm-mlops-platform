.PHONY: help install test format lint clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make format     - Format code with black and isort"
	@echo "  make lint       - Run linting checks"
	@echo "  make clean      - Remove generated files"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/
	mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
