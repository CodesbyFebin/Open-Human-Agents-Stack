.PHONY: up down logs test lint pki clean

up:
	docker compose -f docker/docker-compose.yml up --build -d
	@echo "Control plane: http://localhost:8000/health"
	@echo "Console: http://localhost:3000"

down:
	docker compose -f docker/docker-compose.yml down

logs:
	docker compose -f docker/docker-compose.yml logs -f control-plane

test:
	pytest tests/ -v --tb=short || true

lint:
	python -m compileall backend/ agents/ || true
	npx tsc --noEmit || true

pki:
	bash scripts/bootstrap_pki.sh

clean:
	docker compose -f docker/docker-compose.yml down -v --remove-orphans
