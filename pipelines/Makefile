up:
	@echo "Starting all services..."
	docker compose -f infra/docker-compose.yml --env-file .env up -d

down:
	@echo "Stopping all services..."
	docker compose -f infra/docker-compose.yml down

logs:
	@echo "Stopping all services..."
	docker compose -f infra/docker-compose.yml --env-file .env logs

dev:
	uv run dagster dev

lint:
	@echo "\nLint all files\n--------------"
	uv run ruff check --fix --show-fixes .
	@echo "\nFormat all files\n----------------"
	uv run ruff format .

lint-check:
	@echo "\nLint check\n----------"
	uv run ruff check -e -q .
	@echo "\nFormat check\n------------"
	uv run ruff format --check . || true
