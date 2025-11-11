Use a lake-first, batch-oriented design with content-addressable documents, strong provenance, and an orchestrator that runs the same code locally and in the cloud.

This data pipeline transforms raw data into vector embeddings, knowledge graphs, and other data types/sources  used for RAG and GraphRAG in GenAI applications. 

# Initial Stages
Ingest data, store raw data, and prepare for subsequent information extraction. Not looking for streaming jobs.  Batch jobs are OK since our system can tolerate data that is stale for up to an hour. Non-functional requirements include being able to run on a local machine, easy migration to the cloud, easy on-boarding of new engineers. The data pipeline must support experimentation and observability. 
## Overview

1. **Sources → Ingestion jobs**
    
2. **Staging → Raw object store** (immutable blobs)
    
3. **Registration → Metadata catalog** (provenance + schema)
    
4. **Light normalization → Text-extraction layer** (page/text JSON)
    
5. **Expose assets** for downstream IE, chunking, KG, embeddings.
    

```
┌───────────────┐    ┌─────────────┐    ┌────────────────┐    ┌─────────────────┐
│ Connectors    │──▶ │ Ingestion   │──▶ │ Raw Object     │──▶ │ Text Extraction │
│ (APIs/files)  │    │ Orchestrator│    │ Store (S3/FS)  │    │ (PDF/html>json) │
└───────────────┘    └─────────────┘    └────────────────┘    └─────────────────┘
                         │                      │                    │
                         ▼                      ▼                    ▼
                     ┌─────────┐           ┌──────────┐        ┌─────────────┐
                     │ Lineage │◀─────────▶│ Metadata │◀──────▶│ Asset Views │
                     │ & DQ    │           │ Catalog  │        │ (tables/DU) │
                     └─────────┘           └──────────┘        └─────────────┘
```

## Non-functional alignment

- **Local first, cloud ready:** Docker Compose locally. Same images on ECS/GKE. Object store abstraction: local FS or MinIO → S3. Postgres locally → managed Postgres in cloud.
    
- **Onboarding:** `make up`, sample configs, seeded demo data, devcontainer.
    
- **Batch tolerance:** hourly DAGs. Idempotent tasks keyed by content hash.
    
- **Experimentation:** config-driven connectors and extractors, small sampled datasets, run tags, data versioning.
    
- **Observability:** OpenLineage + Marquez, OpenTelemetry traces, structured logs, data quality checks at boundaries.
    

## Reference stack (pragmatic defaults)

- **Orchestrator:** Dagster (asset-based, easy local UI). Prefect is a lighter alternative.
    
- **Object store:** MinIO locally, S3 in cloud.
    
- **Tabular lake:** Apache Iceberg tables on S3; DuckDB for local query dev.
    
- **Metadata & registry:** Postgres + SQLModel/Prisma; Marquez for lineage; Great Expectations (GX) or Soda for DQ.
    
- **Versioning:** lakeFS overlaying S3 for branches and commits. Simple mode: content-hash paths without lakeFS.
    
- **Text extraction:** Tika + pdfminer + trafilatura/readability + custom HTML cleaners; `unstructured` as a fallback.
    
- **Packaging:** Docker, devcontainer, Makefile, `.env`.
    
- **Auth/secrets:** dotenv locally; cloud secrets manager.
    

## Core data model

**Document ID** = `sha256(content_bytes)`; stable across re-ingests.  
**Source ID** = connector+external key (e.g., `confluence:SPACE-123`).  
**Ingest Run ID** = orchestrator run UUID.

### Raw store layout (immutable)

```
s3://data-lake/raw/source=<src>/ingest_date=YYYY-MM-DD/run_id=<run>/
  sha256=<doc_id>/blob.bin
  sha256=<doc_id>/headers.json
  sha256=<doc_id>/manifest.json
```

- `headers.json`: HTTP/API metadata.
    
- `manifest.json`: `{source_id, doc_id, mime, bytes, fetched_at, url, etag, checksum, license, pii_flags}`.
    

### Text-extraction layer

```
s3://data-lake/staged_text/source=<src>/doc_id=<doc_id>/
  text.jsonl      # [{page, text, char_count, lang, ocr_used}]
  structure.json  # headings, links, tables, images, footnotes
  quality.json    # extraction metrics, language confidence, ocr ratio
```

- Keep **page-level records**; preserves citations for RAG/GraphRAG.
    

### Catalog tables (Iceberg)

- `docs`: one row per `doc_id`.
    
    - cols: `doc_id`, `source_id`, `mime`, `size_bytes`, `ingest_first_at`, `ingest_last_at`, `etag`, `url`, `license`, `hash_alg`, `dq_status`.
        
- `doc_versions`: run-level view, for reproducibility.
    
- `doc_text_pages`: `doc_id`, `page_no`, `lang`, `char_count`, `has_ocr`, `storage_path`.
    
- `events_lineage`: task_name, input_ids, output_ids, run_id, timings.
    
- `dq_findings`: check_name, entity, status, value, run_id.
    

## Ingestion design

- **Connectors** are pure functions: `(config) -> Iterable[FetchedItem]`. No side effects besides returning bytes+metadata.
    
- **Normalization** step standardizes MIME, encoding, and filename.
    
- **Deduplication** by `sha256`. If seen, register new `doc_version` and skip re-store.
    
- **Idempotency**: key tasks by `(source_id, etag|last_modified|sha256)`.
    
- **Retry policy**: exponential backoff; capture raw response in `headers.json` for forensics.
    

### Supported sources

- File drops, S3 buckets, GDrive, Confluence, SharePoint, Git repos, HTTP sitemaps, REST APIs.
    
- For each: implement `discover`, `fetch`, `fingerprint`, `yield`.
    

## Making data available for extraction

- **Access patterns:**
    
    - Downstream IE jobs read from `staged_text` and `docs` tables.
        
    - Provide a small **Data Access SDK**: `get_doc(doc_id)`, `iter_pages(doc_id)`, `search_docs(filters)`, `open_blob(doc_id)`.
        
    - Include DuckDB convenience: `duckdb.sql("select * from docs where ...")`.
        
- **Sampling for experiments:** deterministic reservoir sample by doc_id hash prefix, e.g., `doc_id LIKE '00%'` ≈ 1/256.
    

## Data quality and observability

- **DQ entry checks:** MIME in allowlist, size limits, text density thresholds, language detection, OCR ratio, duplicate rate.
    
- **Extraction checks:** non-empty text, page count sanity, encoding issues, HTML boilerplate percentage.
    
- **Lineage:** emit OpenLineage events per asset. Store run params in catalog for reproducibility.
    
- **Metrics:** per-source fetch rate, bytes/hour, success ratio, median extraction time, dedup hit rate.
    
- **Tracing:** instrument connectors and extractors with OpenTelemetry.
    

## Security and governance

- **PII flags:** classify early with lightweight rules; tag at `doc` and `page` level.
    
- **Licensing:** store license in manifest; enforce allow/deny at orchestrator.
    
- **Isolation:** run untrusted HTML/PDF processing in a sandboxed container.
    

## Local-to-cloud path

- Local: Docker Compose with `minio`, `postgres`, `marquez`, `dagster`, `duckdb` file, and a log volume.
    
- Cloud: swap endpoints via env vars. Same containers. Infra via Terraform. IAM roles for S3 and catalog.
    

## Repo layout

```
/pipeline
  /connectors/             # confluence.py, gdrive.py, s3.py
  /extractors/             # pdf.py, html.py, ocr.py
  /orchestration/          # dagster_assets.py, schedules.py
  /catalog/                # ddl/, migrations/, models.py
  /sdk/                    # client.py, duckdb_helpers.py
  /dq/                     # gx_checks.yml
  /configs/
    sources/               # *.yaml per source
    runtime/               # local.yaml, cloud.yaml
  /infra/                  # docker-compose.yml, terraform/
  /samples/                # demo docs
  Makefile
  devcontainer.json
```

## Config examples

`configs/sources/confluence.yaml`

```yaml
source: confluence
spaces: [ENG, DOCS]
auth: ${CONF_TOKEN}
max_bytes: 50_000_000
include_mime: [text/html, application/pdf]
license: internal
```

`configs/runtime/local.yaml`

```yaml
object_store: s3://minio/data-lake
minio:
  endpoint: http://minio:9000
  access_key: minio
  secret_key: minio123
catalog:
  url: postgresql://postgres:postgres@postgres:5432/catalog
iceberg:
  warehouse: s3://minio/warehouse
observability:
  openlineage_url: http://marquez:5000
```

## Schedules

- **Hourly**: incremental ingest per source.
    
- **Daily**: full reconciliation for drift.
    
- **Post-ingest**: extraction job triggers for new `doc_id`s only.
    

## Why this works for RAG and GraphRAG later

- Stable `doc_id` and page records enable exact citations and chunk lineage.
    
- Structured `structure.json` supports section-aware chunking and graph edges.
    
- Iceberg tables keep joins fast and incremental for entity extraction and graph materialization.
    

## Minimal next steps

1. Scaffold repo with Docker Compose, Dagster, MinIO, Postgres, Marquez.
    
2. Implement one connector (e.g., HTTP sitemap) and one extractor (PDF).
    
3. Create `docs`, `doc_versions`, `doc_text_pages` Iceberg tables.
    
4. Add GX checks and OpenLineage emission.
    
5. Ship a small SDK to read pages and blobs.
    

If you want, I can draft Dagster asset definitions, Iceberg DDL, and the SDK interface next.