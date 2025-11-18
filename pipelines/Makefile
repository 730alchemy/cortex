.PHONY: dev up down

up:
	@echo "Starting all services..."
	docker compose -f infra/docker-compose.yml --env-file .env up -d

down:
	@echo "Stopping all services..."
	docker compose -f infra/docker-compose.yml down

dev:
	uv run dagster dev
