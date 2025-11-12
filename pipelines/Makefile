.PHONY: help up down logs restart reset seed duckdb-shell iceberg-init status clean install

help:
	@echo "Cortex Data Pipeline - Make Targets"
	@echo "===================================="
	@echo "  up              - Start all services"
	@echo "  down            - Stop all services"
	@echo "  logs            - Tail logs from all services"
	@echo "  restart         - Restart all services"
	@echo "  reset           - Stop services and wipe all data volumes"
	@echo "  seed            - Load sample data into watch directory"
	@echo "  duckdb-shell    - Open DuckDB shell connected to Iceberg"
	@echo "  iceberg-init    - Initialize Iceberg catalog and tables"
	@echo "  status          - Show status of all services"
	@echo "  clean           - Remove temporary files and caches"
	@echo "  install         - Install Python dependencies with PDM"

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
	pdm run duckdb pipelines.duckdb

iceberg-init:
	@echo "Initializing Iceberg catalog and tables..."
	pdm run python -m catalog.init_iceberg

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
	@echo "Installing Python dependencies with PDM..."
	pdm install
	@echo "Dependencies installed. Virtual environment ready."
