.PHONY: up down logs test lint e2e pki recovery-drill clean migrate

up:
	docker compose -f docker/docker-compose.yml up --build -d
	@echo ""
	@echo "✓ Control plane: http://localhost:8000/health"
	@echo "✓ Console:       http://localhost:3000"
	@echo "✓ WebSocket:     ws://localhost:8000/ws/telemetry"
	@echo ""
	@curl -sf http://localhost:8000/health | python3 -m json.tool || echo "⚠ Control plane not ready yet"

down:
	docker compose -f docker/docker-compose.yml down

logs:
	docker compose -f docker/docker-compose.yml logs -f control-plane

test:
	pytest tests/ -v --tb=short --timeout=60

lint:
	ruff check backend/ agents/ --strict
	cd ui && npx tsc --noEmit

e2e:
	playwright install --with-deps chromium
	pytest tests/test_e2e_browser.py -v --tb=short

pki:
	bash scripts/bootstrap_pki.sh

recovery-drill:
	bash scripts/recovery_drill.sh

migrate:
	alembic upgrade head

clean:
	docker compose -f docker/docker-compose.yml down -v --remove-orphans
