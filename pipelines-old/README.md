# Cortex Data Pipeline

Lake-first, batch-oriented data pipeline with Apache Iceberg, DuckDB, and Dagster.

## Overview

The Cortex data pipeline ingests documents from various sources, stores them in a content-addressable lakehouse, and prepares them for downstream information extraction, knowledge graph population, and vector embedding generation.

### Key Features

- **Content-addressable storage**: SHA256-based deduplication
- **Iceberg tables**: ACID transactions, time travel, schema evolution
- **DuckDB query engine**: Fast SQL queries without JVM overhead
- **Dagster orchestration**: Asset-based pipeline with sensors
- **Local-first**: Runs entirely on Docker Compose
- **Cloud-ready**: Same code works with S3 and managed services

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- PDM (Python package manager)
- Make
- LLVM and Clang (for building Python C extensions)
  ```bash
  sudo apt-get install llvm clang build-essential
  ```

### 1. Install Dependencies

```bash
cd pipelines
pdm install
```

### 2. Start Services

```bash
make up
```

This starts:
- MinIO (object storage) - http://localhost:9001
- PostgreSQL (Iceberg catalog) - localhost:5432
- Dagster (orchestration) - http://localhost:3000
- Qdrant (vector DB) - http://localhost:6333
- Neo4j (graph DB) - http://localhost:7474
- Marquez (lineage) - http://localhost:5000

### 3. Initialize Iceberg Catalog

```bash
make iceberg-init
```

Creates the catalog tables:
- `catalog.docs` - Document metadata
- `catalog.doc_versions` - Version history
- `catalog.doc_text_pages` - Extracted text (future)
- `catalog.events_lineage` - Data lineage

### 4. Seed Sample Data

```bash
make seed
```

Copies sample files to the watch directory. The Dagster sensor will detect them automatically.

### 5. Monitor Ingestion

Open Dagster UI: http://localhost:3000

- View the `ingest_file_drop` asset
- Check sensor status
- View run history and logs

## Architecture

```
┌──────────────┐    ┌─────────────┐    ┌────────────┐
│ Watch Dir    │───▶│ Dagster     │───▶│ MinIO      │
│ (File Drop)  │    │ (Sensor)    │    │ (Raw Blobs)│
└──────────────┘    └─────────────┘    └────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐    ┌────────────┐
                    │ Iceberg     │◀───│ DuckDB     │
                    │ (Metadata)  │    │ (Queries)  │
                    └─────────────┘    └────────────┘
```

### Data Flow

1. **Watch**: Sensor scans `samples/watch/file_drop/` every 30s
2. **Fetch**: Connector reads file content and metadata
3. **Hash**: Compute SHA256 for content-addressable ID
4. **Dedupe**: Check if doc_id exists in `catalog.docs`
5. **Store**: Upload blob and manifest to MinIO
6. **Catalog**: Write metadata to Iceberg table
7. **Version**: Record ingestion in `doc_versions`
8. **Lineage**: Emit OpenLineage event

### Storage Layout

**MinIO Buckets**:
```
s3://data-lake/
  raw/
    source=file_drop/
      ingest_date=2025-01-11/
        run_id=<uuid>/
          sha256=<doc_id>/
            blob.bin
            manifest.json

s3://warehouse/
  catalog/
    docs/
      metadata/
      data/
    doc_versions/
      metadata/
      data/
```

**Iceberg Tables** (PostgreSQL catalog):
- Metadata stored in `catalog` database
- Parquet data files in `s3://warehouse/`
- Daily partitions by `ingest_date`

## Usage

### Query Documents

```python
from sdk.client import PipelineClient

client = PipelineClient()

# Get document by ID
doc = client.get_doc("abc123...")

# Iterate documents
for doc in client.iter_docs(source_id="file_drop%", limit=10):
    print(doc)

# Get raw content
content = client.open_blob("abc123...")

# Get stats
stats = client.get_stats()
print(f"Total docs: {stats['total_docs']}")
```

### DuckDB Queries

```bash
make duckdb-shell
```

```sql
-- Count documents
SELECT COUNT(*) FROM iceberg_scan('s3://warehouse/catalog/docs');

-- Recent ingestions
SELECT doc_id, source_id, ingest_first_at
FROM iceberg_scan('s3://warehouse/catalog/docs')
ORDER BY ingest_first_at DESC
LIMIT 10;

-- Documents by source
SELECT source_id, COUNT(*) as count
FROM iceberg_scan('s3://warehouse/catalog/docs')
GROUP BY source_id;

-- Time travel (query as of timestamp)
SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs')
FOR SYSTEM_TIME AS OF '2025-01-11 12:00:00';
```

### Managing the Pipeline

```bash
# View all commands
make help

# Stop services
make down

# View logs
make logs

# Restart services
make restart

# Reset (delete all data)
make reset

# Check service status
make status

# Clean temporary files
make clean
```

## Configuration

Configuration files in `configs/`:

- `sources/file_drop.yaml` - File drop connector settings
- `runtime/local.yaml` - Local environment configuration

Environment variables in `infra/.env` (copy from `.env.example`).

## Development

### Project Structure

```
pipelines/
├── connectors/          # Data source connectors
│   ├── base.py
│   └── file_drop.py
├── catalog/             # Iceberg catalog management
│   ├── schemas.py
│   ├── iceberg_catalog.py
│   ├── duckdb_manager.py
│   └── init_iceberg.py
├── orchestration/       # Dagster assets and sensors
│   ├── assets.py
│   ├── sensors.py
│   ├── resources.py
│   ├── definitions.py
│   ├── workspace.yaml
│   └── dagster.yaml
├── sdk/                 # Data access SDK
│   ├── client.py
│   └── duckdb_helpers.py
├── configs/             # Configuration files
│   ├── sources/
│   └── runtime/
├── samples/             # Sample data
│   ├── sample_docs/
│   └── watch/
├── infra/               # Infrastructure
│   ├── docker-compose.yml
│   ├── Dockerfile.dagster
│   └── .env.example
├── pyproject.toml       # Python dependencies
└── Makefile             # Common operations
```

### Adding a New Connector

1. Create `connectors/my_source.py` implementing `Connector` interface
2. Add configuration in `configs/sources/my_source.yaml`
3. Create asset in `orchestration/assets.py`
4. Add sensor if needed in `orchestration/sensors.py`

### Running Tests

```bash
pdm run test
```

### Code Quality

```bash
# Format code
pdm run format

# Lint
pdm run lint

# Type check
pdm run typecheck
```

## Observability

### Dagster UI
- http://localhost:3000
- View asset status, run history, logs
- Manually trigger assets
- Monitor sensors

### MinIO Console
- http://localhost:9001
- Login: minio / minio123
- Browse buckets and objects
- View storage usage

### Marquez (Lineage)
- http://localhost:5000
- Track data lineage
- View dataset dependencies
- Impact analysis

### Neo4j Browser
- http://localhost:7474
- Login: neo4j / cortexpassword
- (Future: populated by downstream jobs)

### Qdrant Dashboard
- http://localhost:6333/dashboard
- (Future: populated by embedding jobs)

## Troubleshooting

### Services won't start

```bash
# Check logs
make logs

# Verify Docker resources
docker ps
docker stats

# Reset and try again
make reset
make up
```

### Sensor not triggering

- Check Dagster daemon is running: `docker ps | grep daemon`
- Verify watch directory exists: `ls samples/watch/file_drop`
- Check sensor status in Dagster UI
- Review daemon logs: `make logs | grep daemon`

### Tables not found

```bash
# Reinitialize Iceberg catalog
make iceberg-init

# Verify tables in PostgreSQL
docker exec -it cortex-postgres psql -U cortex -d catalog -c "\dt"
```

### DuckDB can't read Iceberg

- Ensure MinIO is accessible
- Check S3 credentials in `.env`
- Verify Iceberg extension is loaded: `LOAD iceberg;`

## Next Steps

1. **Text Extraction**: Add extractors for PDF, HTML, etc.
2. **Entity Extraction**: NLP pipeline for entity recognition
3. **Graph Population**: Write entities/relations to Neo4j
4. **Vector Embeddings**: Generate and index embeddings in Qdrant
5. **API Gateway**: Build query API for TUI and web clients
6. **Cloud Deployment**: Terraform modules for AWS/GCP

## License

MIT
