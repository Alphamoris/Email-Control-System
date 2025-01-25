.PHONY: help install dev test lint clean migrate superuser docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  install      Install dependencies and set up development environment"
	@echo "  dev         Start development server"
	@echo "  test        Run tests"
	@echo "  lint        Run linters (black, isort, flake8, mypy)"
	@echo "  clean       Clean up temporary files"
	@echo "  migrate     Run database migrations"
	@echo "  superuser   Create superuser"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run  Run in Docker container"

install:
	python -m venv venv
	./venv/Scripts/activate
	pip install -r requirements.txt
	pre-commit install

dev:
	python scripts/run_dev_server.py

test:
	pytest tests -v --cov=app --cov-report=term-missing

lint:
	black .
	isort .
	flake8 .
	mypy .

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +

migrate:
	python scripts/run_migrations.py

superuser:
	python scripts/create_superuser.py

docker-build:
	docker build -t email-control-backend .

docker-run:
	docker run -p 8000:8000 --env-file .env email-control-backend
