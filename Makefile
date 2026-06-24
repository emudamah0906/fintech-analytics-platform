.PHONY: install dev seed test lint up down

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload

seed:
	python -m app.db.seed

test:
	pytest -q

lint:
	ruff check .

up:
	docker compose up --build

down:
	docker compose down -v
