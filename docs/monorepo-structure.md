Use a domain-oriented monorepo with strict boundaries. Group by KM pipeline stages: ingest → process → store/graph → serve → UI. Keep shared code in `/libs/<lang>`. Orchestrate builds at repo root. This fits polyglot teams and mixed deployables.

## Monorepo Layout

```
/apps
  /cortex-web           # TypeScript app (package.json, pnpm workspace)
  /cortex-tui           # Go TUI
/services
  /cortex-gateway       # Go/TS API edge (OpenAPI)
  /svc-doc-indexer      # Go service (go.mod)
/pipelines              # Python ETL (pyproject.toml, DAGs)
/graph
  /schema               # KG schema + migrations (see below)
  /jobs                 # Go/Python batch jobs touching the graph
  /adapters             # Connectors to graph DB (per lang)
/libs
  /ts/{ui-kit,client-sdk}
  /go/{authz,logging,graph-client}
  /python/{featureflags,graph-client}
/contracts
  /openapi              # REST contracts
  /proto                # gRPC if needed
  /jsonschema           # data contracts for events/files
/infra
  /deploy               # k8s/helm, compose for dev
  /terraform            # cloud resources (graph DB, queues, buckets)
/tools                  # codegen, devcontainers, precommit hooks
/.ci                    # workflows
/Makefile or /Taskfile.yml
```

## Why this works for KM

- Keeps ingestion, transformation, and serving isolated. Minimizes accidental graph coupling.
- Explicit `/graph/schema` centralizes ontology and constraints.
- `/contracts` forces spec-first APIs and data contracts for pipelines and services.
- Each deployable is a true package/module with its own lockfile.

## Pros and cons

**Pros**

- Clear ownership by bounded context.
- Mixed languages per context are allowed without scattering.
- Scales CI via path filters and per-package caches.
- Easier cross-cutting changes with a single PR across pipelines, graph, and API.

**Cons**

- Requires governance to stop “reach-in” imports.
- Shared library curation is ongoing work.
- Repo-wide refactors touch many projects; needs graph-aware build caching.

## Language-specific notes

- **TypeScript**: pnpm workspaces for `/apps/ui-web` and `/libs/ts/*`. Publish internal packages via workspace protocol.
- **Go**: one module per service or grouped with `go.work`. For shared clients, version `/libs/go/*`.
- **Python**: one package per pipeline or job; lock with `uv` or Poetry. No global venvs. DAGs (Airflow/Prefect/Dagster) live under `/pipelines`.

## Knowledge graph schema and migrations

- Pick one and version it in `/graph/schema`:
    - **LPG (Neo4j)**: `migrations/` with Cypher files; enforce with tests.
    - **RDF/OWL**: `ontology.ttl`, SHACL shapes in `shapes.ttl`; validate in CI.
- Maintain a machine-readable changelog and bump a `GRAPH_SCHEMA_VERSION`.
- Generate typed clients into `/libs/*/graph-client` from the schema where possible.

## Contracts and codegen

- Keep OpenAPI/JSON Schema/proto as the source of truth in `/contracts`.
- Generate clients/servers into language libs on CI. Never hand-edit generated code.
- Add contract tests that spin up `/api-gateway` and validate examples from `/contracts`.

## CI/CD shape

- Path-filtered jobs: run only what changed.
- Matrix per language: lint → unit → build → integration.
- Graph-aware caching: start with `actions/cache` + `pnpm store`, Go build cache, Python wheels. Move to **Pants** or **Bazel** when CI time becomes a bottleneck.
- Spin up ephemeral stack via `docker compose` from `/infra/deploy` for integration tests: API + minimal graph DB + a tiny dataset.

## Repo-level tasks (suggested)

- `make bootstrap` → install toolchains, set up workspaces.
- `make lint|test|build [SCOPE=path]` → fan out by language.
- `make e2e` → bring up compose and run end-to-end checks.
- `make codegen` → regenerate from `/contracts` and `/graph/schema`.

## Governance

- Enforce boundaries with:
    
    - Import rules: only import across contexts via `/libs/*`.
    - CODEOWNERS by directory.
    - Pre-commit for formatting and license headers.
    - ADRs in `/docs/adr` for tech choices that affect the tree.

## Alternatives and when to use

- **Bazel/Pants from day 1**: best for very large graphs or strict hermetic builds. Costly to maintain early.

## Bottom line

There is no universal standard. For a KM system with pipelines, services, UIs, and a graph DB, a **domain-oriented layout with versioned schema and contracts** is the most practical default. Start with native tooling and path-filtered CI. Adopt Pants/Bazel only when scale forces it.