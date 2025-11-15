# CLAUDE.md - Cortex Codebase Guide for AI Assistants

> Last Updated: 2025-01-15
> This document provides a comprehensive guide to the Cortex codebase structure, development workflows, and conventions for AI assistants.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Technology Stack](#technology-stack)
4. [Quick Start for Development](#quick-start-for-development)
5. [Architecture & Data Flow](#architecture--data-flow)
6. [Key Components](#key-components)
7. [Development Workflows](#development-workflows)
8. [Testing & Code Quality](#testing--code-quality)
9. [Configuration Management](#configuration-management)
10. [Important Conventions](#important-conventions)
11. [Common Tasks](#common-tasks)
12. [Troubleshooting](#troubleshooting)
13. [Future Development](#future-development)

---

## Project Overview

**Cortex** is an AI-driven knowledge management system that transforms how knowledge is created, stored, and accessed in software development environments.

### Core Mission
- **Shift paradigm**: From "create and find knowledge assets" → "chat with AI-driven systems to create and find knowledge"
- **Make finding knowledge fast and pleasant**
- **Improve knowledge quality** through AI validation and conflict detection
- **Remove ambiguity** about where to add knowledge
- **Transform knowledge** from document-centric to conversation-centric

### Problems Solved
- Related knowledge scattered across multiple sources
- Knowledge conflicts and gaps due to distribution
- Time wasted trying to find and piece together information

### Current State
- **Data Pipeline**: Production-ready for ingestion with Apache Iceberg lakehouse
- **TUI Application**: Initial implementation with stubbed API (awaiting API gateway)
- **API Gateway**: Not yet implemented
- **Knowledge Graph & Vector Search**: Infrastructure ready, not yet populated

---

## Repository Structure

```
cortex/                          # Root directory
├── apps/                        # Application layer
│   └── cortex-tui/             # Go-based Terminal User Interface
│       ├── cmd/cortex-tui/     # Application entry point
│       ├── internal/           # Internal packages
│       │   ├── api/            # API client (currently stubbed)
│       │   ├── config/         # Configuration loading
│       │   ├── models/         # Data models
│       │   └── tui/            # TUI components (Bubbletea)
│       ├── Makefile
│       ├── go.mod
│       └── README.md
│
├── pipelines/                   # Python data pipeline (main component)
│   ├── catalog/                # Iceberg catalog management
│   │   ├── schemas.py          # Table schemas
│   │   ├── iceberg_catalog.py  # Catalog operations
│   │   ├── duckdb_manager.py   # DuckDB connection manager
│   │   └── init_iceberg.py     # Catalog initialization
│   ├── connectors/             # Data source connectors
│   │   ├── base.py             # Abstract connector interface
│   │   └── file_drop.py        # File system connector
│   ├── orchestration/          # Dagster orchestration
│   │   ├── assets.py           # Data assets
│   │   ├── sensors.py          # Event sensors
│   │   ├── resources.py        # Shared resources
│   │   ├── definitions.py      # Central registry
│   │   ├── workspace.yaml      # Workspace config
│   │   └── dagster.yaml        # Dagster config
│   ├── sdk/                    # Data access SDK
│   │   ├── client.py           # PipelineClient
│   │   └── duckdb_helpers.py   # Query helpers
│   ├── configs/                # Configuration files
│   │   ├── sources/            # Source-specific configs
│   │   │   └── file_drop.yaml
│   │   └── runtime/            # Environment configs
│   │       └── local.yaml
│   ├── infra/                  # Docker infrastructure
│   │   ├── docker-compose.yml  # Service definitions
│   │   ├── Dockerfile.dagster  # Dagster container
│   │   └── .env.example        # Environment template
│   ├── samples/                # Sample data
│   │   ├── sample_docs/        # Example documents
│   │   └── watch/              # Watch directories
│   │       └── file_drop/
│   ├── tests/                  # Test suite
│   ├── pyproject.toml          # Python dependencies (uv)
│   ├── Makefile                # Common operations
│   └── README.md
│
├── docs/                        # Documentation
│   ├── adrs/                   # Architecture Decision Records
│   │   └── adr-data-pipeline-orchestration.md
│   ├── ai-chats/               # AI conversation logs
│   ├── notes/                  # Development notes
│   ├── cortex-product-brief.md
│   ├── data-pipeline-architecture.md
│   ├── tui-design.md
│   ├── graph-db-decision.md
│   └── monorepo-structure.md
│
├── Makefile                     # Root-level build orchestration
├── .gitignore                   # Git ignore rules
└── LICENSE                      # MIT License
```

---

## Technology Stack

### Data Pipeline (Python 3.12+)

#### Core Technologies
- **Dagster** (1.6+): Asset-oriented workflow orchestration
  - Chosen over Prefect for experimental capabilities (see ADR)
- **Apache Iceberg**: ACID table format for data lake
- **DuckDB** (0.10+): Fast SQL query engine with Iceberg integration
- **MinIO**: S3-compatible object storage (local development)
- **PostgreSQL**: Iceberg catalog and metadata storage
- **Neo4j Community Edition**: Knowledge graph database
- **Qdrant**: Vector database for embeddings
- **Marquez**: Data lineage tracking with OpenLineage

#### Python Dependencies
```python
# Orchestration
dagster >= 1.6.0
dagster-webserver >= 1.6.0
dagster-postgres >= 0.22.0

# Data Processing
duckdb >= 0.10.0
pyarrow >= 15.0.0
pandas >= 2.2.0

# Storage
boto3 >= 1.34.0
s3fs >= 2024.2.0

# Database
sqlmodel >= 0.0.14
psycopg2-binary >= 2.9.0

# Text Processing
puremagic >= 1.30
chardet >= 5.2.0

# Lineage
openlineage-python >= 1.7.0
openlineage-dagster >= 1.7.0

# Configuration & Utilities
pyyaml >= 6.0
python-dotenv >= 1.0.0
pydantic >= 2.6.0
structlog >= 24.1.0
```

#### Development Tools
```python
# Testing
pytest >= 8.0.0
pytest-cov >= 4.1.0
pytest-mock >= 3.12.0

# Code Quality
black >= 24.1.0  # Line length: 100
ruff >= 0.2.0    # Linting
mypy >= 1.8.0    # Type checking
```

**IMPORTANT**: This project uses **`uv`** for Python package management (switched from PDM in recent commits).

### Terminal UI (Go 1.21+)

#### Framework: Charm.sh Ecosystem
```go
// Main TUI framework
github.com/charmbracelet/bubbletea

// TUI components
github.com/charmbracelet/bubbles

// Styling and layout
github.com/charmbracelet/lipgloss

// Configuration
github.com/BurntSushi/toml
```

### Infrastructure
- **Docker Compose**: Local development orchestration
- **Make**: Build automation across polyglot codebase
- **Git**: Version control

---

## Quick Start for Development

### Prerequisites

**For Data Pipeline:**
- Docker and Docker Compose
- Python 3.12+
- `uv` package manager (install: `pip install uv`)
- Make
- LLVM and Clang for Python C extensions:
  ```bash
  sudo apt-get install llvm clang build-essential
  ```

**For TUI:**
- Go 1.21+
- Make (optional but recommended)

### Data Pipeline Setup

```bash
# 1. Navigate to pipelines directory
cd pipelines

# 2. Install dependencies with uv
uv sync

# 3. Start all Docker services
make up
# This starts: MinIO, PostgreSQL, Dagster, Qdrant, Neo4j, Marquez

# 4. Initialize Iceberg catalog
make iceberg-init

# 5. Seed sample data
make seed

# 6. Open Dagster UI
# http://localhost:3000
```

### TUI Setup

```bash
# 1. Navigate to TUI directory
cd apps/cortex-tui

# 2. Check Go installation
make bootstrap

# 3. Download dependencies
make deps

# 4. Build and run
make dev
```

### Service URLs (Local Development)

| Service | URL | Credentials |
|---------|-----|-------------|
| Dagster UI | http://localhost:3000 | - |
| MinIO Console | http://localhost:9001 | minio / minio123 |
| Neo4j Browser | http://localhost:7474 | neo4j / cortexpassword |
| Qdrant Dashboard | http://localhost:6333/dashboard | - |
| Marquez (Lineage) | http://localhost:5000 | - |
| PostgreSQL | localhost:5432 | cortex / cortexpass / catalog |

---

## Architecture & Data Flow

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Cortex TUI (Go)                          │
│               [Currently uses stubbed API]                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              API Gateway (Future Implementation)             │
└────────────────────────┬─────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Neo4j     │  │   Qdrant    │  │  DuckDB/    │
│  (Graph)    │  │  (Vectors)  │  │  Iceberg    │
└─────────────┘  └─────────────┘  └──────┬──────┘
                                          │
                                          ▼
                         ┌────────────────────────────┐
                         │   Data Pipeline (Dagster)  │
                         └────────────────────────────┘
```

### Data Pipeline Architecture (Lake-First, Batch-Oriented)

**Pipeline Stages:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Watch Dir  │───▶│   Dagster    │───▶│   MinIO     │
│ (File Drop) │    │   (Sensor)   │    │ (Raw Blobs) │
└─────────────┘    └──────┬───────┘    └──────┬──────┘
                          │                    │
                          ▼                    ▼
                   ┌──────────────┐    ┌─────────────┐
                   │   Iceberg    │◀───│   DuckDB    │
                   │  (Metadata)  │    │  (Queries)  │
                   └──────────────┘    └─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   Marquez    │
                   │  (Lineage)   │
                   └──────────────┘
```

### Data Flow Steps

1. **Watch**: Sensor scans watch directories every 30 seconds
2. **Fetch**: Connector reads file content and metadata
3. **Hash**: Compute SHA256 for content-addressable ID (`doc_id`)
4. **Dedupe**: Check if `doc_id` exists in catalog
5. **Store**: Upload blob and manifest to MinIO (S3)
6. **Catalog**: Write metadata to Iceberg tables via DuckDB
7. **Version**: Record ingestion in `doc_versions` table
8. **Lineage**: Emit OpenLineage events to Marquez

### Storage Layout

**MinIO Buckets (S3-compatible):**
```
s3://data-lake/
  raw/
    source=<source_name>/
      ingest_date=YYYY-MM-DD/
        run_id=<uuid>/
          sha256=<doc_id>/
            blob.bin          # Raw document content
            manifest.json     # Metadata (source_id, mime, size, etc.)

s3://warehouse/
  catalog/
    docs/                     # Iceberg table data
      metadata/
      data/
    doc_versions/
      metadata/
      data/
    doc_text_pages/
      metadata/
      data/
    events_lineage/
      metadata/
      data/
```

**Iceberg Tables (DuckDB Schema: `catalog`):**

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `docs` | Document metadata | doc_id, source_id, mime, size_bytes, ingest_first_at, ingest_last_at |
| `doc_versions` | Version history | doc_id, run_id, ingested_at |
| `doc_text_pages` | Extracted text | doc_id, page_num, text (future) |
| `events_lineage` | Data lineage | event_type, dataset, timestamp |

---

## Key Components

### 1. Connectors (`/pipelines/connectors/`)

**Pattern**: Abstract base class with three methods:

```python
class Connector(ABC):
    @abstractmethod
    def discover(self) -> List[str]:
        """List available items"""

    @abstractmethod
    def fetch(self, external_id: str) -> FetchedItem:
        """Retrieve content and metadata"""

    @abstractmethod
    def fingerprint(self, external_id: str) -> Optional[str]:
        """Get etag/checksum for change detection"""
```

**Current Implementation:**
- `FileDropConnector`: Watches local directory for files

**Returned Data**: `FetchedItem` dataclass
```python
@dataclass
class FetchedItem:
    content: bytes
    source_id: str
    mime_type: str
    size_bytes: int
    url: Optional[str]
    etag: Optional[str]
    license: str
    metadata: Dict[str, Any]  # Source-specific attributes
```

### 2. Orchestration (`/pipelines/orchestration/`)

**Dagster Assets** (`assets.py`):
- `ingest_file_drop`: Main ingestion asset
  - Fetches from connector
  - Computes SHA256 doc_id
  - Checks for duplicates
  - Stores in MinIO and Iceberg
  - Returns stats (discovered, ingested, skipped, errors)

**Sensors** (`sensors.py`):
- `file_drop_sensor`: Monitors watch directory
  - Runs every 30 seconds
  - Tracks file modification times via cursor
  - Triggers `RunRequest` when new/modified files detected

**Resources** (`resources.py`):
- `MinIOResource`: S3 client wrapper with upload/download methods
- `DuckDBResource`: DuckDB manager with Iceberg configuration

**Definitions** (`definitions.py`):
- Central registry for all assets, sensors, and resources
- Configures structured logging (JSON format)

### 3. Catalog Management (`/pipelines/catalog/`)

**DuckDB Manager**:
- Manages DuckDB connection with Iceberg extension
- Configures S3 secrets for MinIO access
- Provides query execution interface

**Iceberg Initialization**:
- Creates namespace and tables
- SQL DDL for docs, versions, pages, lineage tables
- Run with: `make iceberg-init` or `uv run python -m catalog.init_iceberg`

### 4. SDK (`/pipelines/sdk/`)

**PipelineClient**: Data access interface

```python
from sdk.client import PipelineClient

client = PipelineClient()

# Get document by ID
doc = client.get_doc("sha256_hash...")

# Iterate documents with filters
for doc in client.iter_docs(source_id="file_drop%", limit=10):
    print(doc)

# Download raw content
content = client.open_blob("sha256_hash...")

# Execute custom SQL
results = client.query("SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs') LIMIT 5")

# Get statistics
stats = client.get_stats()
print(f"Total docs: {stats['total_docs']}")
```

### 5. TUI Application (`/apps/cortex-tui/`)

**Architecture**: Bubbletea's Elm Architecture (Model-Update-View)

**Components**:
- `config/`: TOML configuration loading
- `api/`: HTTP client (currently stubbed with dummy data)
- `models/`: Data models (Project, Message, MessagePair, InformationSource)
- `tui/`: View components (Model, QueryView, ProjectView)

**Features**:
- Tab-based navigation (Query Tab, Project Tab)
- Project selector with keyboard navigation
- Chat interface for queries
- Information sources display
- Session logging to `/tmp/cortex-tui/cortex-tui.log`

**Keyboard Shortcuts**:
- `Tab` / `Shift+Tab`: Switch tabs
- `↑` / `↓`: Navigate projects or messages
- `Enter`: Submit query
- `Ctrl+K`: Toggle collapse/expand message pair
- `Ctrl+L`: Clear chat history
- `q` / `Ctrl+C`: Quit

**Configuration** (`cortex-tui.toml`):
```toml
[cortex-api]
url = "http://localhost:8080"
username = ""
password = ""
database = ""

[logging]
level = "info"  # debug, info, warn, error
```

---

## Development Workflows

### Data Pipeline Development

#### Local Development (Two Options)

**Option 1: Full Docker Stack**
```bash
cd pipelines
make up          # Start all services
make logs        # View logs
```

**Option 2: Local Python with Containerized Services**
```bash
cd pipelines

# Start only infrastructure services
docker-compose up postgres minio neo4j qdrant -d

# Run Dagster locally
uv run dagster dev -m orchestration
```

#### Common Commands

```bash
# Service Management
make up              # Start all services
make down            # Stop services
make restart         # Restart services
make status          # Show service status
make logs            # Tail logs

# Data Management
make seed            # Load sample data
make reset           # Delete all data volumes (WARNING: destructive)
make clean           # Clean temporary files

# Development
make iceberg-init    # Initialize Iceberg catalog
make duckdb-shell    # Open DuckDB REPL
uv run dagster dev -m orchestration  # Run Dagster dev server

# Testing
uvx pytest tests/ -v              # Run tests
uvx pytest tests/ -v --cov        # Run tests with coverage
uvx ruff check .                  # Lint
uvx black .                       # Format
uvx mypy .                        # Type check
```

#### Adding a New Connector

1. **Create connector class** in `connectors/my_source.py`:
   ```python
   from connectors.base import Connector, FetchedItem

   class MySourceConnector(Connector):
       def discover(self) -> List[str]:
           # Implementation

       def fetch(self, external_id: str) -> FetchedItem:
           # Implementation

       def fingerprint(self, external_id: str) -> Optional[str]:
           # Implementation
   ```

2. **Add configuration** in `configs/sources/my_source.yaml`:
   ```yaml
   source: my_source
   api_endpoint: https://api.example.com
   api_key: ${API_KEY}
   ```

3. **Create asset** in `orchestration/assets.py`:
   ```python
   @asset
   def ingest_my_source(
       context: AssetExecutionContext,
       minio: MinIOResource,
       duckdb: DuckDBResource,
   ):
       # Implementation
   ```

4. **Add sensor** (if needed) in `orchestration/sensors.py`

5. **Register** in `orchestration/definitions.py`

### TUI Development

#### Development Commands

```bash
cd apps/cortex-tui

# Development Workflow
make bootstrap       # Check Go installation
make deps            # Download dependencies
make fmt             # Format code
make build           # Build binary
make run             # Build and run
make dev             # Format, build, and run (recommended)

# Testing
make test            # Run Go tests
make lint            # Run golangci-lint

# Clean
make clean           # Remove build artifacts
```

#### Updating the TUI

**To update the API client** (when real API is available):

1. Edit `internal/api/client.go`
2. Replace stubbed methods with real HTTP calls
3. Update models in `internal/models/models.go` if needed
4. Test with `make test`

**To add new views**:

1. Create new file in `internal/tui/`
2. Implement view function returning `string`
3. Add to model's `View()` method in `internal/tui/model.go`

### Monorepo Management

**Root Makefile** delegates to language-specific builds:
```bash
# From root directory
make bootstrap       # Setup all development environments
make build           # Build all projects (currently just TUI)
make test            # Run all tests
make lint            # Lint all projects
make fmt             # Format all code
make clean           # Clean all build artifacts
```

**Each component has its own package manager**:
- Python: `pipelines/pyproject.toml` with `uv`
- Go: `apps/cortex-tui/go.mod` with Go modules

**Shared nothing architecture**: No code sharing between apps and pipelines (different languages)

---

## Testing & Code Quality

### Python Pipeline Testing

**Test Structure**:
```
pipelines/tests/
├── __init__.py
├── fixtures/           # Sample files for testing
├── test_connectors.py
├── test_catalog.py
└── test_sdk.py
```

**Running Tests**:
```bash
cd pipelines

# Run all tests
uvx pytest tests/ -v

# Run with coverage
uvx pytest tests/ -v --cov

# Run specific test
uvx pytest tests/test_connectors.py::test_file_drop -v

# Run with debugging
uvx pytest tests/ -v -s
```

**Test Configuration** (in `pyproject.toml`):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --cov=. --cov-report=term-missing"
```

### Python Code Quality

**Formatting** (Black):
```bash
uvx black .                    # Format all files
uvx black --check .            # Check without modifying
```

**Linting** (Ruff):
```bash
uvx ruff check .               # Lint all files
uvx ruff check . --fix         # Auto-fix issues
```

**Type Checking** (MyPy):
```bash
uvx mypy .                     # Type check all files
```

**Configuration** (in `pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ['py312']

[tool.ruff]
line-length = 100
target-version = "py312"
select = ["E", "W", "F", "I", "B", "C4"]
ignore = ["E501"]  # Line too long (handled by black)

[tool.mypy]
python_version = "3.12"
warn_return_any = true
disallow_untyped_defs = false
ignore_missing_imports = true
```

### Go Testing

**Running Tests**:
```bash
cd apps/cortex-tui

make test              # Run all tests
go test ./... -v       # Verbose output
go test ./... -cover   # With coverage
```

**Code Quality**:
```bash
make fmt               # Format with gofmt
make lint              # Run golangci-lint
```

### Pre-commit Recommendations

**Create `.pre-commit-config.yaml`** (recommended but not yet implemented):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        files: ^pipelines/

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        files: ^pipelines/

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        files: ^pipelines/
```

---

## Configuration Management

### Pipeline Configuration

**Location**: `pipelines/configs/`

**Source Configurations** (`configs/sources/*.yaml`):

```yaml
# configs/sources/file_drop.yaml
source: file_drop
watch_directory: samples/watch/file_drop
recursive: false
file_extensions: [.md, .txt, .pdf, .html, .json, .yaml]
max_file_size_mb: 50
license: internal
scan_interval_seconds: 30
```

**Runtime Configuration** (`configs/runtime/local.yaml`):

```yaml
object_store:
  endpoint: http://localhost:9000
  access_key: minio
  secret_key: minio123
  bucket_raw: data-lake
  bucket_warehouse: warehouse

iceberg:
  catalog_uri: postgresql://cortex:cortexpass@localhost:5432/catalog
  warehouse_path: s3://warehouse/

duckdb:
  database_path: pipelines.duckdb

postgres:
  host: localhost
  port: 5432
  database: catalog
  user: cortex
  password: cortexpass

# ... (qdrant, neo4j, marquez configs)
```

**Environment Variables** (`pipelines/infra/.env`):

Copy from `.env.example` and customize:
```bash
# MinIO
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123

# PostgreSQL
POSTGRES_USER=cortex
POSTGRES_PASSWORD=cortexpass
POSTGRES_DB=catalog

# Neo4j
NEO4J_AUTH=neo4j/cortexpassword
```

### TUI Configuration

**Location**: `./cortex-tui.toml` or `~/.config/cortex/tui.toml`

```toml
[cortex-api]
url = "http://localhost:8080"
username = ""
password = ""
database = ""

[logging]
level = "info"  # debug, info, warn, error
```

### Docker Compose Services

**File**: `pipelines/infra/docker-compose.yml`

**Services**:
- `minio`: Object storage (9000, 9001)
- `postgres`: Metadata catalog (5432)
- `qdrant`: Vector DB (6333, 6334)
- `neo4j`: Graph DB (7474, 7687)
- `marquez`: Lineage (5000, 5001)
- `dagster-user-code`: gRPC server (4000)
- `dagster-webserver`: Web UI (3000)
- `dagster-daemon`: Schedules and sensors

**Network**: All services on `cortex-network` bridge

**Volumes**: Persistent storage for all databases

---

## Important Conventions

### Naming Conventions

**Python** (PEP 8):
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPERCASE_WITH_UNDERSCORES`
- Private members: `_leading_underscore`
- Files: `lowercase_with_underscores.py`

**Go**:
- Exported (public): `PascalCase`
- Unexported (private): `camelCase`
- Files: `lowercase.go`
- Test files: `*_test.go`

**Environment Variables**:
- All: `UPPERCASE_WITH_UNDERSCORES`

**Configuration Files**:
- Python runtime: YAML (`.yaml`)
- Go app config: TOML (`.toml`)
- Docker: `.env` file

### Code Organization Patterns

**Python Modules**:
- Organize by functionality (connectors, catalog, orchestration, sdk)
- Each module has `__init__.py`
- Keep modules focused and cohesive

**Go Packages**:
- Organize by layer (api, config, models, tui/internal)
- Use `internal/` for private packages
- Keep package dependencies acyclic

### Data Patterns

1. **Content-Addressable Storage**
   - All documents identified by SHA256 hash
   - Same content = same `doc_id`
   - Enables automatic deduplication

2. **Idempotency**
   - Always check if `doc_id` exists before re-ingestion
   - Safe to re-run ingestion pipelines
   - No duplicates in catalog

3. **Version Tracking**
   - Every ingestion recorded in `doc_versions`
   - Track when document was first and last seen
   - Enables time-travel queries

4. **Immutable Raw Storage**
   - Never modify original blobs in MinIO
   - Only append to Iceberg tables
   - Enables audit trails

5. **Partition by Date**
   - Iceberg tables partitioned by `ingest_date`
   - Improves query performance
   - Enables efficient data management

6. **Lineage First**
   - All transformations emit OpenLineage events
   - Track data provenance
   - Enable impact analysis

### Development Patterns

1. **Local-First, Cloud-Ready**
   - Same code runs locally (MinIO) and cloud (S3)
   - Use environment-specific configs
   - No code changes for deployment

2. **Asset-Oriented**
   - Data as first-class citizens in Dagster
   - Assets define "what", not "when"
   - Sensors trigger based on events

3. **Sensor-Driven**
   - Event-based triggers rather than cron schedules
   - React to file system changes, API events, etc.
   - More efficient than polling

4. **Structured Logging**
   - JSON logs with `structlog` for observability
   - Include context (run_id, doc_id, source)
   - Machine-readable for aggregation

5. **Thin Abstractions**
   - Minimal wrappers over databases
   - Prefer direct access when appropriate
   - Don't over-engineer

---

## Common Tasks

### Working with Documents

**Query documents via SDK**:
```python
from sdk.client import PipelineClient

client = PipelineClient()

# Get specific document
doc = client.get_doc("sha256_hash_here")
print(f"Source: {doc['source_id']}")
print(f"MIME: {doc['mime']}")
print(f"Size: {doc['size_bytes']}")

# Download raw content
blob = client.open_blob("sha256_hash_here")
with open("output.bin", "wb") as f:
    f.write(blob)

# Search documents
for doc in client.iter_docs(mime="text/markdown", limit=20):
    print(doc['source_id'])
```

**Query via DuckDB**:
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

-- Documents by MIME type
SELECT mime, COUNT(*) as count
FROM iceberg_scan('s3://warehouse/catalog/docs')
GROUP BY mime;

-- Time travel (query as of timestamp)
SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs')
FOR SYSTEM_TIME AS OF '2025-01-15 12:00:00';
```

### Working with Dagster

**Manually trigger asset materialization**:
1. Open Dagster UI: http://localhost:3000
2. Navigate to Assets
3. Select `ingest_file_drop`
4. Click "Materialize"

**View sensor status**:
1. Open Dagster UI
2. Navigate to Automation → Sensors
3. Check `file_drop_sensor` status
4. View cursor state and tick history

**View run logs**:
1. Navigate to Runs
2. Select a run
3. View logs, compute logs, and structured logs

**Check daemon status**:
```bash
docker logs cortex-dagster-daemon -f
```

### Managing Services

**Start/Stop**:
```bash
cd pipelines

# Start all
make up

# Stop all (preserve data)
make down

# Stop and remove volumes (WARNING: deletes all data)
make reset

# Restart specific service
docker-compose restart dagster-webserver

# View logs for specific service
docker logs cortex-dagster-webserver -f
```

**Check service health**:
```bash
# View status of all services
make status

# Check specific service
docker ps | grep dagster

# View resource usage
docker stats
```

### Adding Sample Data

**Add to watch directory**:
```bash
# Copy files to watch directory
cp my_document.md pipelines/samples/watch/file_drop/

# Sensor will detect within 30 seconds
# Watch Dagster UI for ingestion run
```

**Verify ingestion**:
```bash
# Query via SDK
cd pipelines
uv run python -c "
from sdk.client import PipelineClient
c = PipelineClient()
stats = c.get_stats()
print(f'Total docs: {stats[\"total_docs\"]}')
"

# Or via DuckDB
make duckdb-shell
# Then: SELECT COUNT(*) FROM iceberg_scan('s3://warehouse/catalog/docs');
```

### Viewing Lineage

**Marquez UI**:
1. Open http://localhost:5000
2. Browse datasets
3. View lineage graph
4. Check run history

### Git Workflow

**Current Branch**: `claude/claude-md-mi0hp6nrwdznrbb4-014TpkPYWhKJ3kkhtKWm7C2H`

**Making Changes**:
```bash
# Make your changes
# ...

# Stage changes
git add .

# Commit
git commit -m "feat: your change description"

# Push to remote branch
git push -u origin claude/claude-md-mi0hp6nrwdznrbb4-014TpkPYWhKJ3kkhtKWm7C2H
```

**IMPORTANT**:
- Always push to branches starting with `claude/` and ending with session ID
- Push will fail with 403 if branch naming is incorrect
- Retry network failures up to 4 times with exponential backoff (2s, 4s, 8s, 16s)

---

## Troubleshooting

### Services Won't Start

**Symptoms**: Docker Compose fails to start services

**Solutions**:
```bash
# Check Docker daemon
systemctl status docker

# Check logs
make logs

# Verify Docker resources (need 4GB+ RAM)
docker stats

# Clean up and restart
make reset
make up
```

### Sensor Not Triggering

**Symptoms**: Files added to watch directory but not ingested

**Solutions**:
1. **Check daemon is running**:
   ```bash
   docker ps | grep daemon
   docker logs cortex-dagster-daemon -f
   ```

2. **Verify watch directory**:
   ```bash
   ls -la pipelines/samples/watch/file_drop/
   ```

3. **Check sensor status** in Dagster UI:
   - Navigate to Automation → Sensors
   - Verify `file_drop_sensor` is running
   - Check tick history

4. **Check sensor logs**:
   ```bash
   make logs | grep file_drop_sensor
   ```

### Tables Not Found

**Symptoms**: DuckDB queries fail with "table not found"

**Solutions**:
```bash
# Reinitialize Iceberg catalog
make iceberg-init

# Verify tables in PostgreSQL
docker exec -it cortex-postgres psql -U cortex -d catalog -c "\dt"

# Check MinIO buckets
# Open http://localhost:9001 (minio/minio123)
# Verify warehouse/catalog/ exists
```

### DuckDB Can't Read Iceberg

**Symptoms**: `iceberg_scan()` fails with S3 errors

**Solutions**:
1. **Check MinIO is running**:
   ```bash
   docker ps | grep minio
   ```

2. **Verify S3 credentials** in `.env`:
   ```bash
   cat pipelines/infra/.env | grep MINIO
   ```

3. **Check DuckDB Iceberg extension**:
   ```bash
   make duckdb-shell
   # Then: LOAD iceberg; SHOW iceberg;
   ```

4. **Test MinIO connectivity**:
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

### Python Import Errors

**Symptoms**: `ModuleNotFoundError` when running Python code

**Solutions**:
```bash
cd pipelines

# Ensure uv environment is synced
uv sync

# Check Python version
python --version  # Should be 3.12+

# Verify packages installed
uv pip list
```

### Go Build Failures

**Symptoms**: `make build` fails in TUI

**Solutions**:
```bash
cd apps/cortex-tui

# Check Go version
go version  # Should be 1.21+

# Clean and rebuild
make clean
go mod tidy
make deps
make build
```

### Data Not Appearing in Neo4j/Qdrant

**Status**: This is expected. Entity extraction and embedding generation are not yet implemented.

**Future**: Wait for downstream pipeline jobs to be implemented.

---

## Future Development

### Roadmap

**Next Steps** (in priority order):

1. **Text Extraction Pipeline**
   - PDF extraction (PyMuPDF, pdfplumber)
   - HTML extraction (BeautifulSoup, trafilatura)
   - OCR for images (Tesseract, Azure Vision)
   - Store extracted text in `doc_text_pages` table

2. **Entity Extraction Pipeline**
   - NER (spaCy, Hugging Face transformers)
   - Relationship extraction (OpenAI, Claude API)
   - Custom extractors for code, API specs, etc.

3. **Knowledge Graph Population**
   - Write entities to Neo4j
   - Create relationships
   - Implement graph algorithms (PageRank, community detection)

4. **Vector Embeddings**
   - Generate embeddings (OpenAI, Cohere, local models)
   - Index in Qdrant
   - Implement hybrid search (semantic + keyword)

5. **API Gateway Implementation**
   - RESTful API (Go or TypeScript)
   - Endpoints: projects, queries, sources, documents
   - Authentication and authorization
   - Rate limiting

6. **TUI Integration**
   - Connect TUI to real API
   - Implement chat with knowledge base
   - Add document preview

7. **Cloud Deployment**
   - Terraform modules for AWS/GCP
   - Replace MinIO with S3/GCS
   - Managed PostgreSQL, Neo4j, Qdrant
   - CI/CD pipelines

8. **Multi-Model Experimentation**
   - Use Dagster partitions for different models
   - A/B testing for extraction quality
   - Model performance tracking

### Open Questions

**Architecture**:
- What constitutes a "knowledge unit"? (document, section, paragraph, sentence?)
- How to handle knowledge versioning and contradictions?
- Should extraction be manual → heuristic → LLM-based pipeline?

**Technology**:
- Python vs TypeScript for LLM orchestration?
- Local models vs API-based models?
- How to handle rate limits and costs?

**Data Quality**:
- How to validate extracted entities?
- How to detect knowledge conflicts?
- What metrics indicate knowledge quality?

### Contributing

**When Adding New Features**:

1. **Follow ADR process** for architectural decisions
   - Create new ADR in `docs/adrs/`
   - Format: `adr-NNNN-short-title.md`
   - Include context, decision, consequences

2. **Write structured logs**:
   ```python
   # Python
   import structlog
   logger = structlog.get_logger()
   logger.info("document_ingested", doc_id=doc_id, source=source_id)
   ```

3. **Add OpenLineage events** for data transformations:
   ```python
   from openlineage.client import OpenLineageClient
   # Emit start/complete/fail events
   ```

4. **Update Iceberg schemas** via `catalog/init_iceberg.py`:
   - Add new columns
   - Create new tables
   - Run `make iceberg-init`

5. **Document in README files**:
   - Update relevant README
   - Add examples and usage
   - Update this CLAUDE.md if architectural

6. **Write tests**:
   - Unit tests for business logic
   - Integration tests for end-to-end flows
   - Use fixtures for sample data

---

## AI Assistant Guidelines

### When Working on Data Pipeline

**CRITICAL**:
- **Always use `uv`** for Python package management (recently switched from PDM)
- Run `make iceberg-init` after schema changes
- All timestamps in UTC
- Content-addressable means same content = same `doc_id`
- Never modify blobs in MinIO, only append to Iceberg tables

**Helpful Commands**:
- Check sensor logs: `docker logs cortex-dagster-daemon -f`
- Fast queries: `make duckdb-shell`
- View lineage: http://localhost:5000
- Browse MinIO: http://localhost:9001

**Common Pitfalls**:
- Forgetting to initialize Iceberg after schema changes
- Not handling duplicate `doc_id` correctly
- Missing OpenLineage events for new transformations
- Hardcoding paths instead of using configs

### When Working on TUI

**CRITICAL**:
- Use Bubbletea's Elm Architecture (Init, Update, View)
- Messages flow unidirectionally
- Commands (`tea.Cmd`) for async operations
- API client is currently stubbed (real implementation pending)

**Config Locations**:
- `./cortex-tui.toml`
- `~/.config/cortex/tui.toml`

**Common Pitfalls**:
- Blocking operations in Update() method (use Cmd instead)
- Modifying model state outside Update()
- Forgetting to return Cmd from Update()

### When Adding Connectors

**Required Methods**:
1. `discover()`: List available items
2. `fetch(external_id)`: Retrieve content and metadata
3. `fingerprint(external_id)`: Get etag for change detection

**Don't Forget**:
- Add config in `configs/sources/`
- Create Dagster asset in `orchestration/assets.py`
- Add sensor if real-time needed
- Register in `orchestration/definitions.py`
- Write tests in `tests/test_connectors.py`

### When Modifying Schemas

**Process**:
1. Update `catalog/schemas.py`
2. Update `catalog/init_iceberg.py` with new DDL
3. Run `make reset` (WARNING: deletes all data)
4. Run `make up`
5. Run `make iceberg-init`
6. Update SDK queries if needed
7. Update tests

### Best Practices

**Documentation**:
- Update README files for user-facing changes
- Update this CLAUDE.md for architectural changes
- Create ADRs for significant decisions
- Document in code with docstrings/comments

**Testing**:
- Write tests before implementation (TDD)
- Test happy path and error cases
- Use fixtures for sample data
- Mock external services

**Code Quality**:
- Run formatters before committing
- Fix linter warnings
- Type hint Python code
- Use Go's `gofmt` and `golangci-lint`

**Git Commits**:
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Write clear commit messages
- One logical change per commit
- Reference issues if applicable

**Performance**:
- Batch operations when possible
- Use DuckDB for fast queries
- Partition Iceberg tables appropriately
- Monitor Dagster run times

---

## Quick Reference

### Essential Files

| File | Purpose |
|------|---------|
| `pipelines/pyproject.toml` | Python dependencies (uv) |
| `pipelines/Makefile` | Pipeline commands |
| `pipelines/orchestration/definitions.py` | Dagster central registry |
| `pipelines/catalog/init_iceberg.py` | Catalog initialization |
| `pipelines/sdk/client.py` | Data access SDK |
| `apps/cortex-tui/cmd/cortex-tui/main.go` | TUI entry point |
| `apps/cortex-tui/internal/tui/model.go` | TUI main model |
| `pipelines/infra/docker-compose.yml` | Service definitions |
| `docs/data-pipeline-architecture.md` | Architecture deep dive |

### Essential Commands

```bash
# Pipeline
cd pipelines && make up          # Start services
cd pipelines && make iceberg-init  # Initialize catalog
cd pipelines && make seed         # Load sample data
cd pipelines && make duckdb-shell # Open DuckDB REPL

# TUI
cd apps/cortex-tui && make dev   # Format, build, run

# Root
make build                        # Build all projects
make test                         # Run all tests

# Git
git push -u origin claude/...     # Push to branch
```

### Essential URLs

- Dagster: http://localhost:3000
- MinIO: http://localhost:9001 (minio/minio123)
- Neo4j: http://localhost:7474 (neo4j/cortexpassword)
- Marquez: http://localhost:5000

---

## Version History

| Date | Changes |
|------|---------|
| 2025-01-15 | Initial CLAUDE.md creation |

---

**End of CLAUDE.md**

For questions or clarifications, refer to:
- `docs/` directory for detailed documentation
- `README.md` files in each component
- Architecture Decision Records in `docs/adrs/`
