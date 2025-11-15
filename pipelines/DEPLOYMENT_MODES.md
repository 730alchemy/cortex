# Dagster Deployment Modes

This guide explains how to run the Cortex data pipeline with different deployment configurations, supporting both containerized and local development workflows.

## Overview

The pipeline supports three deployment modes:

1. **Docker Mode** - Everything runs in containers (production-like)
2. **Local Mode** - Everything runs on your local machine (fast iteration)
3. **Hybrid Mode** - Mix of Docker and local (best of both worlds)

## Quick Start

### Docker Mode (Default)

All code and infrastructure in containers:

```bash
cd pipelines
make dev-docker
```

Open http://localhost:3000 to see Dagster UI.

### Local Mode

Infrastructure in Docker, code runs locally for fast iteration:

```bash
cd pipelines

# Start infrastructure services
make up

# Run Dagster locally with hot reload
make dev-local
```

### Hybrid Mode

Infrastructure + webserver in Docker, run specific code locations locally:

```bash
cd pipelines

# Terminal 1: Start infrastructure and Dagster webserver
make dev-hybrid

# Terminal 2: Run your code server locally
make code-server
```

Then edit `orchestration/workspace.hybrid.yaml` to point to your local server.

---

## Detailed Configuration

### 1. Docker Mode

**When to use:**
- Production deployments
- Testing the full containerized stack
- Ensuring consistency across environments

**Workspace file:** `orchestration/workspace.docker.yaml`

```yaml
load_from:
  - grpc_server:
      host: dagster-user-code
      port: 4000
      location_name: cortex_pipeline
```

**How it works:**
- All services defined in `infra/docker-compose.yml` start
- User code runs in `dagster-user-code` container
- Webserver connects to code server via Docker network
- Hot reload requires rebuilding containers

**Start:**
```bash
make dev-docker
# or
cd infra && docker compose up -d
```

---

### 2. Local Mode

**When to use:**
- Active development with hot reload
- Debugging Python code with breakpoints
- Fast iteration without rebuilding containers

**Workspace file:** `orchestration/workspace.local.yaml`

```yaml
load_from:
  - python_file:
      relative_path: definitions.py
      location_name: cortex_pipeline
      working_directory: /home/user/cortex/pipelines/orchestration
```

**How it works:**
- Infrastructure runs in Docker (Postgres, MinIO, etc.)
- Dagster webserver and daemon run locally
- Code loads directly from Python files
- Changes reload automatically

**Prerequisites:**
```bash
# Install dependencies
make install

# Start infrastructure
make up
```

**Start:**
```bash
make dev-local
# or
DAGSTER_HOME=$(pwd)/orchestration uv run dagster dev -w orchestration/workspace.local.yaml
```

**Environment variables:**
The local mode connects to containerized services on `localhost`:
- PostgreSQL: `localhost:5432`
- MinIO: `localhost:9000`
- Qdrant: `localhost:6333`
- Neo4j: `localhost:7687`

---

### 3. Hybrid Mode

**When to use:**
- Developing multiple projects/code locations
- Some code in Docker, some local
- Testing cross-location dependencies
- Stable webserver UI while iterating on code

**Workspace file:** `orchestration/workspace.hybrid.yaml`

```yaml
load_from:
  # Code location in Docker
  - grpc_server:
      host: dagster-user-code
      port: 4000
      location_name: cortex_pipeline_docker

  # Code location running locally
  - grpc_server:
      host: host.docker.internal  # Special DNS name to reach host
      port: 4001
      location_name: cortex_pipeline_local
```

**How it works:**
- Infrastructure + webserver + daemon run in Docker
- Webserver uses `host.docker.internal` to reach local code servers
- Each code location runs as a gRPC server (Docker or local)
- Mix and match as needed

**Setup:**

**Terminal 1 - Infrastructure:**
```bash
make dev-hybrid
# This starts: postgres, minio, webserver, daemon (NOT user code container)
```

**Terminal 2 - Local code server:**
```bash
make code-server
# Starts gRPC server on port 4000
```

**For multiple projects:**

Terminal 2 - ProjectA (local):
```bash
cd /home/user/cortex/projecta
DAGSTER_POSTGRES_HOST=localhost \
DAGSTER_POSTGRES_PORT=5432 \
DAGSTER_POSTGRES_DB=dagster \
DAGSTER_POSTGRES_USER=cortex \
DAGSTER_POSTGRES_PASSWORD=cortex \
MINIO_ENDPOINT=http://localhost:9000 \
MINIO_ACCESS_KEY=minio \
MINIO_SECRET_KEY=minio123 \
uv run dagster code-server start -h 0.0.0.0 -p 4001 -m orchestration.definitions
```

Terminal 3 - ProjectB (local):
```bash
cd /home/user/cortex/projectb
DAGSTER_POSTGRES_HOST=localhost \
  ... (same env vars) ... \
uv run dagster code-server start -h 0.0.0.0 -p 4002 -m orchestration.definitions
```

Update `workspace.hybrid.yaml`:
```yaml
load_from:
  - grpc_server:
      host: host.docker.internal
      port: 4001
      location_name: projecta_local
  - grpc_server:
      host: host.docker.internal
      port: 4002
      location_name: projectb_local
```

---

## Advanced: Python-Based Workspace

For maximum flexibility, use `orchestration/workspace.py`:

```python
# Auto-detects mode from environment variables
import os
from dagster._core.workspace.load_target import PythonFileTarget, GrpcServerTarget

mode = os.getenv("WORKSPACE_MODE", "docker")

if mode == "local":
    workspace = [
        PythonFileTarget(
            python_file="orchestration/definitions.py",
            location_name="cortex_pipeline",
        )
    ]
else:  # docker
    workspace = [
        GrpcServerTarget(
            host="dagster-user-code",
            port=4000,
            location_name="cortex_pipeline",
        )
    ]
```

**Usage:**
```bash
# Docker mode
dagster-webserver -w orchestration/workspace.py

# Local mode
WORKSPACE_MODE=local dagster-webserver -w orchestration/workspace.py

# Per-project control
PROJECTA_MODE=docker PROJECTB_MODE=local dagster-webserver -w orchestration/workspace.py
```

---

## Cross-Location Dependencies

When you have multiple projects with dependencies:

**ProjectA** (provides asset1):
```python
# projecta/orchestration/assets.py
from dagster import asset

@asset
def asset1():
    return {"data": [1, 2, 3]}
```

**ProjectB** (depends on asset1):
```python
# projectb/orchestration/assets.py
from dagster import asset, AssetKey, AssetIn

@asset(ins={"asset1": AssetIn(key=AssetKey("asset1"))})
def asset2(context, asset1):
    # Dagster tracks the dependency
    # Use shared storage to access data
    return process(asset1)
```

**Important:** Cross-location assets need shared storage:
- Use I/O managers (Iceberg, S3, etc.)
- Pass data via MinIO, PostgreSQL, or other shared stores
- Metadata flows through Dagster, data flows through storage

---

## Networking Reference

### Docker → Docker
Services use Docker network names:
- `postgres` (not `localhost`)
- `minio` (not `localhost`)
- `dagster-user-code` (container name)

### Local → Docker
Local processes use exposed ports:
- `localhost:5432` (PostgreSQL)
- `localhost:9000` (MinIO)
- `localhost:4000` (code server)

### Docker → Local
Containers use `host.docker.internal`:
- `host.docker.internal:4000` (local code server)
- Enabled via `extra_hosts` in docker-compose.yml

---

## Troubleshooting

### "Cannot connect to code server"

**Docker mode:**
```bash
# Check if container is running
docker ps | grep dagster-user-code

# Check logs
docker logs cortex-dagster-user-code
```

**Local mode:**
```bash
# Verify gRPC server is listening
lsof -i :4000

# Check Python process
ps aux | grep dagster
```

**Hybrid mode:**
```bash
# Test connectivity from container
docker exec cortex-dagster-webserver curl http://host.docker.internal:4000

# Check workspace config
docker exec cortex-dagster-webserver cat /opt/dagster/dagster_home/workspace.yaml
```

### "Database connection refused"

**From local code:**
- Use `DAGSTER_POSTGRES_HOST=localhost`
- Ensure `make up` has started Postgres

**From container:**
- Use `DAGSTER_POSTGRES_HOST=postgres`
- Check Docker network: `docker network inspect cortex-network`

### "Code changes not reflecting"

**Docker mode:**
```bash
# Rebuild and restart
docker compose -f infra/docker-compose.yml up --build -d dagster-user-code
```

**Local mode:**
- Changes auto-reload in `dagster dev`
- Check terminal for reload messages

**Hybrid mode:**
- Restart local code server: `Ctrl+C` then `make code-server`
- Click "Reload All" in Dagster UI

---

## Summary

| Mode | Webserver | Code | Best For |
|------|-----------|------|----------|
| **Docker** | Docker | Docker | Production, CI/CD |
| **Local** | Local | Local | Fast iteration, debugging |
| **Hybrid** | Docker | Mixed | Multi-project development |

**Commands:**
- `make dev-docker` - Everything in Docker
- `make dev-local` - Everything local
- `make dev-hybrid` - Infrastructure in Docker, code flexible
- `make code-server` - Start local gRPC code server

**Workspace files:**
- `workspace.docker.yaml` - All Docker
- `workspace.local.yaml` - All local
- `workspace.hybrid.yaml` - Mixed deployment
- `workspace.py` - Dynamic/environment-based

Choose the mode that fits your workflow and switch between them as needed!
