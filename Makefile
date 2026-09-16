.PHONY: help setup dev test run lint clean docker-up docker-down seed

help:
	@echo "SpaceLoop Development & Operational Commands:"
	@echo "  make setup        Install dependencies and seed database"
	@echo "  make dev          Start development server with live reload"
	@echo "  make test         Execute all unit, security, and functional tests"
	@echo "  make seed         Seed database with high-density campus micro-spaces"
	@echo "  make docker-up    Start full containerized stack via Docker Compose"
	@echo "  make docker-down  Stop containerized stack"
	@echo "  make clean        Remove Python bytecode and caches"

setup:
	@bash scripts/setup.sh

dev:
	@bash scripts/dev.sh

test:
	@python3 -W ignore -m unittest discover -s tests -p "test_*.py"
	@python3 -W ignore -m unittest verify_spaceloop.py
	@python3 -W ignore -m unittest test_security.py
	@python3 -W ignore -m unittest test_all_features_functional.py

run:
	@python3 app.py

seed:
	@python3 scripts/seed_db.py

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

docker-up:
	@docker compose up --build -d

docker-down:
	@docker compose down
