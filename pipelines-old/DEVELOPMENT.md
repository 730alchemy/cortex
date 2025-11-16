# Development Guide

Guide for developing and extending the Cortex data pipeline.

## Development Environment Setup

### 1. Clone and Install

```bash
git checkout pipeline
cd pipelines
pdm install --dev
```

This installs:
- Production dependencies
- Development tools (pytest, black, ruff, mypy)
- Pre-commit hooks (optional)

### 2. Start Infrastructure

```bash
make up
```

Wait for all services to be healthy (~30 seconds on first run).

### 3. Initialize Database

```bash
make iceberg-init
```

## Development Workflow

### Running the Pipeline Locally

**Option 1: Docker (Production-like)**

```bash
make up
# Pipeline runs in containers
# Access Dagster UI at http://localhost:3000
```

**Option 2: Local Python (Faster iteration)**

```bash
# Start only data services
cd infra
docker-compose up postgres minio neo4j qdrant -d

# Run Dagster locally
pdm run dagster dev -m orchestration
```

This allows hot-reloading of Python code without rebuilding containers.

### Adding a New Connector

1. **Create connector class** in `connectors/your_source.py`:

```python
from connectors.base import Connector, FetchedItem

class YourSourceConnector(Connector):
    def discover(self) -> Iterator[str]:
        # Return list of external IDs
        pass

    def fetch(self, external_id: str) -> FetchedItem:
        # Fetch content and metadata
        pass

    def fingerprint(self, external_id: str) -> str:
        # Return change detection fingerprint
        pass
```

2. **Add configuration** in `configs/sources/your_source.yaml`:

```yaml
source: your_source
api_endpoint: https://api.example.com
auth_token: ${YOUR_SOURCE_TOKEN}
```

3. **Create Dagster asset** in `orchestration/assets.py`:

```python
@asset(description="Ingest from your source")
def ingest_your_source(
    context: AssetExecutionContext,
    minio: MinIOResource,
    iceberg_catalog: IcebergCatalogResource,
):
    connector = YourSourceConnector(...)
    # Similar logic to ingest_file_drop
    pass
```

4. **Add sensor** (if needed) in `orchestration/sensors.py`:

```python
@sensor(name="your_source_sensor")
def your_source_sensor(context):
    # Check for new data
    # Return RunRequest if found
    pass
```

5. **Register in definitions**:

```python
# orchestration/definitions.py
all_sensors.append(sensors.your_source_sensor)
```

### Working with Iceberg Tables

**Add a new table**:

1. Define schema in `catalog/schemas.py`:

```python
MY_TABLE_SCHEMA = Schema(
    NestedField(1, "id", StringType(), required=True),
    NestedField(2, "data", StringType(), required=False),
    identifier_field_ids=[1],
)

MY_TABLE_PARTITION_SPEC = PartitionSpec(
    PartitionField(source_id=2, field_id=1000, transform=DayTransform(), name="date")
)

TABLE_DEFINITIONS["my_table"] = {
    "schema": MY_TABLE_SCHEMA,
    "partition_spec": MY_TABLE_PARTITION_SPEC,
    "description": "My custom table"
}
```

2. Run `make iceberg-init` to create it.

**Query table**:

```python
from catalog.iceberg_catalog import get_iceberg_catalog_manager

catalog_mgr = get_iceberg_catalog_manager()
table = catalog_mgr.load_table("my_table")

# Scan table
df = table.scan().to_pandas()

# Append data
table.append({"id": "123", "data": "test"})
```

### Testing

**Unit Tests**:

```bash
pdm run pytest tests/unit/ -v
```

**Integration Tests** (requires services running):

```bash
make up
pdm run pytest tests/integration/ -v
```

**Test a specific module**:

```bash
pdm run pytest tests/unit/test_file_drop.py -v
```

**Test structure**:

```
tests/
├── unit/
│   ├── test_connectors.py
│   ├── test_catalog.py
│   └── test_sdk.py
├── integration/
│   ├── test_ingestion_e2e.py
│   └── test_queries.py
└── fixtures/
    └── sample_files/
```

### Code Quality

**Format code**:

```bash
pdm run format
```

**Lint**:

```bash
pdm run lint
```

**Type check**:

```bash
pdm run typecheck
```

**All checks**:

```bash
pdm run format && pdm run lint && pdm run typecheck && pdm run test
```

## Debugging

### Dagster Asset Debugging

1. Open Dagster UI: http://localhost:3000
2. Navigate to asset
3. Click "Materialize" to run manually
4. View logs in real-time
5. Inspect run details and lineage

**Add debug logging in assets**:

```python
@asset
def my_asset(context: AssetExecutionContext):
    context.log.info("Debug message")
    context.log.warning("Warning message")
    context.log.error("Error message")
```

### DuckDB Debugging

```bash
make duckdb-shell
```

```sql
-- Check Iceberg metadata
DESCRIBE iceberg_scan('s3://warehouse/catalog/docs');

-- View table schema
SHOW CREATE TABLE iceberg_catalog.docs;

-- Explain query plan
EXPLAIN SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs') WHERE doc_id = '...';
```

### MinIO Debugging

Access MinIO Console: http://localhost:9001

- Browse buckets
- View object metadata
- Check storage policies
- Download files for inspection

### PostgreSQL Debugging

```bash
docker exec -it cortex-postgres psql -U cortex -d catalog
```

```sql
-- List Iceberg metadata tables
\dt

-- View catalog tables
SELECT * FROM iceberg_tables;

-- Check snapshots
SELECT * FROM iceberg_snapshots;
```

### Sensor Debugging

Sensors run in the Dagster daemon. Check logs:

```bash
docker logs cortex-dagster-daemon -f
```

Common issues:
- Cursor not updating: Check `context.update_cursor()`
- Sensor not running: Verify daemon is started
- Rate limiting: Adjust `minimum_interval_seconds`

## Performance Tuning

### Ingestion Throughput

**Batch inserts** instead of row-by-row:

```python
# Slow
for item in items:
    table.append(item)

# Fast
batch = [item for item in items]
table.append_batch(batch)
```

**Parallel processing** with Dagster partitions:

```python
from dagster import DynamicPartitionsDefinition

@asset(partitions_def=DynamicPartitionsDefinition(name="sources"))
def ingest_partitioned(context):
    partition_key = context.partition_key
    # Process only this partition
```

### Query Performance

**Use partition pruning**:

```sql
-- Slow (scans all partitions)
SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs');

-- Fast (prunes partitions)
SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs')
WHERE ingest_first_at >= '2025-01-11'::TIMESTAMP;
```

**Use column projection**:

```sql
-- Slow (reads all columns)
SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs');

-- Fast (reads only needed columns)
SELECT doc_id, source_id FROM iceberg_scan('s3://warehouse/catalog/docs');
```

### Iceberg Compaction

Periodically compact small files:

```python
table = catalog.load_table("catalog.docs")
table.compact_files()
```

Add as a scheduled Dagster job for automatic maintenance.

## Common Patterns

### Content-Addressable Storage

All documents use SHA256 hash as `doc_id`:

```python
import hashlib

doc_id = hashlib.sha256(content).hexdigest()
```

### Idempotent Processing

Always check if already processed:

```python
existing = table.scan(row_filter=f"doc_id = '{doc_id}'").to_arrow()
if len(existing) > 0:
    # Already processed, skip
    return
```

### Version Tracking

Record every ingestion in `doc_versions`:

```python
doc_versions_table.append({
    "doc_id": doc_id,
    "run_id": context.run.run_id,
    "source_id": source_id,
    "ingest_at": datetime.utcnow(),
})
```

### Lineage Tracking

Emit OpenLineage events:

```python
from openlineage.client import OpenLineageClient

client = OpenLineageClient()
client.emit(
    RunEvent(
        eventType="COMPLETE",
        inputs=[Dataset(namespace="file", name=source_id)],
        outputs=[Dataset(namespace="iceberg", name="catalog.docs")],
    )
)
```

## Environment Variables

Reference for all environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MINIO_ENDPOINT` | MinIO URL | `http://localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minio` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minio123` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_USER` | PostgreSQL user | `cortex` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `cortex` |
| `POSTGRES_DB` | PostgreSQL database | `catalog` |
| `WAREHOUSE_PATH` | Iceberg warehouse | `s3://warehouse` |
| `WATCH_DIRECTORY` | File drop path | `samples/watch/file_drop` |
| `DAGSTER_HOME` | Dagster home dir | `/opt/dagster/dagster_home` |

## Troubleshooting

### "Table not found" errors

```bash
make iceberg-init
```

### "S3 connection refused"

Check MinIO is running:

```bash
docker ps | grep minio
curl http://localhost:9000/minio/health/live
```

### Sensor not triggering

1. Check daemon is running: `docker ps | grep daemon`
2. Verify watch directory exists and has files
3. Check sensor interval: `minimum_interval_seconds`
4. Review daemon logs: `make logs | grep daemon`

### Out of disk space

```bash
# Clean Docker volumes
make reset

# Clean DuckDB files
make clean

# Prune Docker system
docker system prune -af --volumes
```

## Contributing

1. Create feature branch from `pipeline`
2. Make changes
3. Run all checks: `make format lint typecheck test`
4. Commit with descriptive message
5. Open pull request

## Additional Resources

- [Apache Iceberg Docs](https://iceberg.apache.org/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Dagster Documentation](https://docs.dagster.io/)
- [PyIceberg API Reference](https://py.iceberg.apache.org/)
