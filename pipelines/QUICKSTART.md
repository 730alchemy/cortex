# Quick Start Guide

Get the Cortex data pipeline running in 5 minutes.

## Prerequisites

- Docker Desktop running
- Python 3.12+
- PDM installed: `pip install pdm`
- LLVM and Clang (for building Python C extensions)
  ```bash
  sudo apt-get install llvm clang build-essential
  ```

## Steps

### 1. Install Python Dependencies

```bash
cd pipelines
pdm install
```

### 2. Start All Services

```bash
make up
```

**What this does**:
- Starts MinIO, PostgreSQL, Dagster, Neo4j, Qdrant, Marquez
- Creates S3 buckets (data-lake, warehouse)
- Launches Dagster webserver and daemon

**Wait ~60 seconds** for all services to be healthy.

### 3. Initialize Iceberg Tables

```bash
make iceberg-init
```

**What this does**:
- Connects to PostgreSQL
- Creates Iceberg catalog namespace
- Creates 4 tables: docs, doc_versions, doc_text_pages, events_lineage

### 4. Test Ingestion

```bash
make seed
```

**What this does**:
- Copies 3 sample files to `samples/watch/file_drop/`
- Dagster sensor detects files within 30 seconds
- Files are ingested automatically

### 5. Verify Ingestion

**Option A: Dagster UI**

1. Open http://localhost:3000
2. Click "Assets"
3. Find `ingest_file_drop`
4. View recent runs and logs

**Option B: DuckDB Query**

```bash
make duckdb-shell
```

```sql
SELECT doc_id, source_id, mime, size_bytes
FROM iceberg_scan('s3://warehouse/catalog/docs');
```

You should see 3 documents!

## What's Next?

### Explore the Data

**View document stats**:

```python
from sdk.client import PipelineClient

client = PipelineClient()
stats = client.get_stats()
print(stats)
```

**Query documents**:

```python
for doc in client.iter_docs(limit=10):
    print(f"{doc['doc_id'][:16]}... - {doc['source_id']}")
```

**Get raw content**:

```python
content = client.open_blob(doc_id)
print(content.decode('utf-8'))
```

### Add More Files

```bash
# Copy your own files
cp ~/Documents/my_file.md pipelines/samples/watch/file_drop/

# Watch the sensor trigger in Dagster UI
# Check logs: make logs | grep sensor
```

### Explore the UIs

- **Dagster**: http://localhost:3000 - Pipeline orchestration
- **MinIO**: http://localhost:9001 - Object storage (minio/minio123)
- **Neo4j**: http://localhost:7474 - Graph database (neo4j/cortexpassword)
- **Marquez**: http://localhost:5000 - Data lineage
- **Qdrant**: http://localhost:6333/dashboard - Vector search

## Troubleshooting

### Services won't start

```bash
# Check Docker resources (need 8GB RAM)
docker stats

# View logs
make logs

# Try resetting
make reset
make up
```

### Sensor not triggering

```bash
# Check daemon is running
docker ps | grep daemon

# View daemon logs
docker logs cortex-dagster-daemon -f

# Manually trigger in Dagster UI
# Go to Assets > ingest_file_drop > Materialize
```

### Can't query tables

```bash
# Reinitialize
make iceberg-init

# Check PostgreSQL
docker exec -it cortex-postgres psql -U cortex -d catalog -c "SELECT * FROM iceberg_tables;"
```

## Clean Up

```bash
# Stop services
make down

# Stop and delete all data
make reset
```

## Next Steps

- Read [README.md](./README.md) for detailed architecture
- Read [DEVELOPMENT.md](./DEVELOPMENT.md) for development guide
- Add text extraction (PDF, HTML)
- Build entity extraction pipeline
- Populate Neo4j knowledge graph
- Generate vector embeddings
