.PHONY: help up down logs restart reset seed duckdb-shell iceberg-init status clean install
.PHONY: dev-docker dev-local dev-hybrid code-server

help:
	@echo "Cortex Data Pipeline - Make Targets"
	@echo "===================================="
	@echo "Infrastructure:"
	@echo "  up              - Start all services (Docker mode)"
	@echo "  down            - Stop all services"
	@echo "  logs            - Tail logs from all services"
	@echo "  restart         - Restart all services"
	@echo "  reset           - Stop services and wipe all data volumes"
	@echo "  status          - Show status of all services"
	@echo ""
	@echo "Development Modes:"
	@echo "  dev-docker      - Run Dagster with all code in Docker"
	@echo "  dev-local       - Run Dagster with all code locally"
	@echo "  dev-hybrid      - Run Dagster with hybrid config (some Docker, some local)"
	@echo "  code-server     - Start local code server on port 4000"
	@echo ""
	@echo "Data Operations:"
	@echo "  seed            - Load sample data into watch directory"
	@echo "  duckdb-shell    - Open DuckDB shell connected to Iceberg"
	@echo "  iceberg-init    - Initialize Iceberg catalog and tables"
	@echo ""
	@echo "Development Tools:"
	@echo "  install         - Install Python dependencies with uv"
	@echo "  clean           - Remove temporary files and caches"
	@echo "  test            - Run tests"
	@echo "  lint            - Run linter"
	@echo "  format          - Format code"

up:
	@echo "Starting all services..."
	cd infra && docker compose up -d
	@echo "Services starting. Web UIs:"
	@echo "  - Dagster:  http://localhost:3000"
	@echo "  - MinIO:    http://localhost:9001 (user: minio, pass: minio123)"
	@echo "  - Neo4j:    http://localhost:7474 (user: neo4j, pass: cortexpassword)"
	@echo "  - Marquez:  http://localhost:5000"
	@echo "  - Qdrant:   http://localhost:6333/dashboard"

down:
	@echo "Stopping all services..."
	cd infra && docker compose down

logs:
	@echo "Tailing logs (Ctrl+C to exit)..."
	cd infra && docker compose logs -f

restart:
	@echo "Restarting all services..."
	cd infra && docker compose restart

reset:
	@echo "WARNING: This will delete all data volumes!"
	@bash -c 'read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd infra && docker compose down -v; \
		echo "All volumes deleted. Run '\''make up'\'' to start fresh."; \
	fi'

seed:
	@echo "Seeding sample data into watch directory..."
	mkdir -p samples/watch/file_drop
	cp samples/sample_docs/* samples/watch/file_drop/ 2>/dev/null || echo "No sample docs to copy"
	@echo "Sample files copied to samples/watch/file_drop/"
	@echo "The Dagster sensor will detect and ingest them automatically."

duckdb-shell:
	@echo "Opening DuckDB shell..."
	@echo "Run: .open pipelines.duckdb"
	@echo "Then: SELECT * FROM iceberg_catalog.docs LIMIT 10;"
	uv run duckdb pipelines.duckdb

iceberg-init:
	@echo "Initializing Iceberg catalog and tables..."
	uv run python -m catalog.init_iceberg

status:
	@echo "Service Status:"
	@cd infra && docker compose ps

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f pipelines.duckdb pipelines.duckdb.wal 2>/dev/null || true
	@echo "Clean complete."

install:
	@echo "Installing Python dependencies with uv ..."
	uv sync
	@echo "Dependencies installed. Virtual environment ready."

dagster-dev:
	uv run dagster dev -m orchestration

# Development modes
dev-docker:
	@echo "Starting Dagster with Docker workspace (all code in containers)..."
	@echo "Using workspace: orchestration/workspace.docker.yaml"
	@echo "Starting services with docker-compose..."
	cd infra && docker compose up -d
	@echo ""
	@echo "Dagster UI: http://localhost:3000"
	@echo "All code locations running in Docker containers"

dev-local:
	@echo "Starting Dagster with local workspace (all code runs locally)..."
	@echo "Using workspace: orchestration/workspace.local.yaml"
	@echo "Make sure infrastructure services are running (make up)"
	@echo ""
	@echo "Starting Dagster dev server..."
	DAGSTER_HOME=$$(pwd)/orchestration uv run dagster dev -w orchestration/workspace.local.yaml

dev-hybrid:
	@echo "Starting Dagster with hybrid workspace..."
	@echo "Using workspace: orchestration/workspace.hybrid.yaml"
	@echo ""
	@echo "Infrastructure services will run in Docker"
	@echo "You can start local code servers with: make code-server"
	@echo ""
	cd infra && docker compose up dagster-webserver dagster-daemon postgres minio qdrant neo4j marquez -d
	@echo ""
	@echo "Dagster UI: http://localhost:3000"
	@echo "Start your local code servers in separate terminals"

code-server:
	@echo "Starting local Dagster code server on port 4000..."
	@echo "This will serve the 'orchestration' module via gRPC"
	@echo "Configure workspace.yaml to connect to: localhost:4000"
	@echo ""
	DAGSTER_POSTGRES_HOST=localhost \
	DAGSTER_POSTGRES_PORT=5432 \
	DAGSTER_POSTGRES_DB=dagster \
	DAGSTER_POSTGRES_USER=cortex \
	DAGSTER_POSTGRES_PASSWORD=cortex \
	MINIO_ENDPOINT=http://localhost:9000 \
	MINIO_ACCESS_KEY=minio \
	MINIO_SECRET_KEY=minio123 \
	uv run dagster code-server start -h 0.0.0.0 -p 4000 -m orchestration.definitions

test:
	uvx pytest tests/ -v

lint:
	uvx ruff check .

format:
	uvx black .

typecheck:
	uvx mypy .

