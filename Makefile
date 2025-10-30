.PHONY: help install test clean format lint run

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make format     - Format code with black and isort"
	@echo "  make lint       - Run linting with flake8"
	@echo "  make clean      - Clean up generated files"
	@echo "  make run        - Run the main application"

install:
	pip install -r requirements.txt

test:
	pytest

format:
	black src tests examples
	isort src tests examples

lint:
	flake8 src tests examples

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/

run:
	python src/main.py

all: format lint test


