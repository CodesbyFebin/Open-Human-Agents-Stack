.PHONY: up down test lint migrate backup pki

up:
	docker compose -f docker/docker-compose.yml up --build

down:
	docker compose -f docker/docker-compose.yml down

test:
	pytest -q tests/

lint:
	python -m compileall backend/ || true
	npx tsc --noEmit || true

migrate:
	python scripts/migrate.py

backup:
	bash scripts/backup.sh

pki:
	bash scripts/bootstrap_pki.sh
