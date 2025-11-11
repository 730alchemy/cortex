# Cortex Data Pipeline Architectures

A compact reference for high-level pipeline patterns that transform unstructured and semi-structured data into embeddings and knowledge graphs.
## Architecture Options

### Lakehouse + Batch Orchestration

**When:** large backfills, diverse sources, cost control.

- **Ingest:** connectors → object store (raw zone) with immutable files + metadata.
- **Normalize:** Spark/DuckDB/Trino → bronze/silver tables.
- **NLP/IE:** distributed NER, coref, entity linking, relation extraction, PII redaction.
- **Outputs:**
  - Embeddings: chunked docs → embedding jobs → vector index build.
  - KG: entity/relation tables → graph loader (Neo4j/Neptune/GraphDB).
- **Governance:** data contracts, Great Expectations, lineage.
- **Orchestration:** Airflow/Dagster/Prefect; backfills, retries, SLAs.
- **Serving:** unified retrieval API (BM25 + vector + graph hops).
- **Trade-offs:** strongest governance and reproducibility; higher latency.

---

### Streaming-First (Kappa)

**When:** near-real-time enrichment; continuous updates.

- **Ingest:** Kafka/PubSub/Kinesis with Schema Registry; CDC from sources.
- **Stream processing:** Flink/kSQL/Spark Streaming for parse/filter/light NLP.
- **Async heavy NLP:** event fan-out to workers (Ray/Dask/Batch).
- **State:** compacted topics for dedup; candidate stores for resolution.
- **Outputs:** upsert embeddings into vector DB; upsert triples/edges into graph DB; versioned subgraphs.
- **Ops:** exactly-once semantics, idempotent sinks, DLQs, lag SLOs.
- **Trade-offs:** lowest latency; higher operational complexity and cost.

---

### Event-Driven Microservices + Lakehouse

**When:** many independent teams; clear domain boundaries.

- **Services:** ingest, parsing, entity-resolution, relation-extraction, chunking, embedding, graph-writer.
- **Contracts:** versioned protobuf/Avro; outbox pattern for reliable publish.
- **Storage:** lakehouse for raw + curated data; domain tables per service.
- **Coordination:** choreography via events; sagas for long-running steps.
- **Observability:** traces per document ID; SLOs per topic.
- **Trade-offs:** team scalability; cross-service governance overhead.

---

### Serverless Minimal Viable Pipeline

**When:** small team, moderate scale, spiky loads.

- **Ingest:** cloud functions → object store.
- **Orchestrate:** Step Functions/Workflows queue tasks.
- **NLP:** serverless Spark or on-demand Ray; models cached in images.
- **Vector/Graph:** managed services for fast start.
- **Governance:** lightweight checks; dataset snapshots per run.
- **Trade-offs:** fastest to ship; throughput and control limits.

---

### Graph-First Core + Derived Embeddings

**When:** ontology is strategic and needs strict semantics.

- **Modeling:** ontology + data contracts; map sources to entities/relations first.
- **Pipeline:** parse → canonicalize → entity resolution → graph upsert; relations as first-class.
- **Embeddings:** combine graph and text (GraphSAGE/node2vec + text embeddings) for hybrid retrieval.
- **Reasoning:** rules/SHACL for constraints; inference writes back to graph.
- **Trade-offs:** strongest knowledge integrity; heavier upfront modeling.

---

#### Modeling Step Frequency and Triggers

The modeling step in the Graph-First Core + Derived Embeddings architecture occurs continuously, not as a one-time task. It evolves alongside the data and ontology lifecycle.

**Cadences**

- **Initial design:** one-time setup to define the base ontology and core schemas.
- **Continuous evolution:** incremental, backward-compatible updates as new data types or relationships emerge.
- **Periodic releases:** formal ontology versions (e.g., monthly or quarterly) for bundled breaking changes.

**Primary triggers**

- **New sources or entities:** onboarding data or concepts outside the existing ontology.
- **Upstream drift:** schema or field name changes in Notion, GitHub, or other inputs.
- **Extraction feedback:** low precision/recall in entity/relation extraction or a rise in unknown entity types.
- **Integrity violations:** SHACL or rule failures, orphan nodes, or inconsistent edges.
- **Query or serving gaps:** missing graph paths that block user queries or degrade retrieval.
- **Performance and scaling:** graph hotspots, skewed degree distributions, or traversal inefficiencies.
- **Governance or compliance:** new data-handling rules, access controls, or lineage requirements.
- **Product evolution:** new features or analytics that require extended semantics.

**Operational practice**

- Propose → analyze impact → prototype on a shadow graph → dual-write old/new → migrate → release new ontology version.
- Tag every embedding, index, and model with `ontology_version` for consistency during migration.

---

## Cross-Cutting Components

- **Chunking:** semantic + structural; store lineage to source and entity IDs.
- **Entity Resolution:** blocking keys + embeddings + rules; canonical IDs stable and versioned.
- **Privacy/Security:** PII detection/redaction, ACLs, encryption, audit logs.
- **Model Ops:** registry, versioned embeddings (model\_id, dim, params), A/B for retrieval quality.
- **Indexing:** HNSW or IVF-PQ; compaction; drift detection; re-embed schedule.
- **Quality:** doc- and edge-level checks; sampling harness for precision/recall of extraction.
- **APIs:** single retrieval endpoint with keyword, vector, and graph traversals; merged answers with citations and provenance.

---

## Quick Selection Guide

- Need sub-second freshness → **Streaming-First**.
- Need compliance, reproducibility, big backfills → **Lakehouse + Batch**.
- Many teams and domains → **Event-Driven Microservices**.
- Prototype or uncertain scale → **Serverless Minimal**.
- Mission-critical ontology and reasoning → **Graph-First**.

---

## Object Store Purpose and Recommendations

### Value

- **Replay & reprocessing:** you will re-run extraction/embeddings when models change. Raw, immutable bytes avoid refetching from Notion/GitHub and protect you from API drift or outages.
- **Provenance & audits:** store the exact payload plus source IDs, commit SHAs, Notion page IDs, timestamps, and signatures. Enables debug and legal holds.
- **Idempotency & dedupe:** content-addressed keys (e.g., SHA256 of normalized bytes) prevent double-processing of repeated webhooks.
- **Deletes & retention:** upstream data can be edited or deleted. You control lifecycle, encryption, and WORM policies.
- **Vendor risk & rate limits:** you are insulated from API throttling and schema changes.
- **Cost:** object storage is cheaper than keeping long-retention queues or constantly rehydrating from APIs.

### When you can skip it

- Prototype scale, low compliance needs.
- You trust upstream history as your immutable source and accept coupling:
  - GitHub: commit history is durable; you can treat the repo itself as the “raw store.”
  - Notion: weaker history and API limits; skipping a raw store is risky.
- Strict data-minimization forbids storing raw copies.

### Minimal reference flow

- Webhook → verify signature → enqueue → normalize → **write raw snapshot to object store** (`/source={notion|github}/id=/ts=/sha=`; store headers, delivery ID).
- Emit events for downstream: chunk → embed → vector upsert; entity/resolution → graph upsert.
- Use the object store for backfills and model re-runs; enforce lifecycle rules and encryption.

If you insist on no object store, at least keep: long-retention event log, deterministic fetchers to reconstruct state, and robust backfill jobs.

---

## Normalization Explanation, Motive, and Options

### Explanation

Normalization is the process of transforming heterogeneous raw inputs—such as JSON payloads from Notion or GitHub webhooks—into a uniform schema and file format. It standardizes field names, types, and structures, producing consistent datasets that can be reliably consumed by downstream NLP, embedding, and graph-building stages.

### Motive

- **Uniformity:** downstream systems expect consistent structures.
- **Validation:** ensures required fields, types, and constraints before processing.
- **Traceability:** makes every normalized record traceable to its source payload and timestamp.
- **Reusability:** allows shared analytics and enrichment tools to operate on the same schema.
- **Change resilience:** decouples data consumers from upstream schema drift.
- **Performance:** columnar formats (Parquet, Delta) optimize batch and query efficiency.

### Options

1. **Schema-on-write (Lakehouse style):** enforce strict schema during normalization; reject or quarantine invalid records.
2. **Schema-on-read (Semi-structured zone):** store normalized JSON but interpret structure dynamically when read.
3. **Hybrid:** write structured core fields plus a JSON blob for evolving or unknown attributes.
4. **Event-based normalization:** apply per-source mapping functions (e.g., Notion pages vs. GitHub commits) producing standard entity types (Document, Commit, PageChange).
5. **Incremental normalization:** detect deltas from prior versions, storing change events rather than full snapshots.

Normalization typically outputs bronze (raw structured), silver (validated/clean), and gold (curated) layers to support iterative refinement and lineage tracking.

## Local Prototyping

You can prototype all five locally. Use small fixtures, CPU-only models, and Docker Compose.

## Shared local baseline

- **Containers:** Docker Compose. One network. Bind mounts for hot-reload.
- **Raw store:** MinIO (S3-compatible). Lifecycle off. Versioning on.
- **Vector DB:** Qdrant or pgvector in Postgres.
- **Graph DB:** Neo4j (community) or Memgraph.
- **Search:** OpenSearch or Tantivy-based Lite.
- **Models:** sentence-transformers CPU. Cache under a volume.
- **Orchestrator:** Prefect/Dagster local. Task logs to stdout.
- **Webhook replay:** save raw payloads; `curl` replays; optionally ngrok for live.
- **Data contracts:** JSON Schema files in repo; validate in CI.

---

## 1) Lakehouse + Batch

**Core stack:** MinIO, DuckDB + Polars, Prefect/Dagster, Qdrant, Neo4j.\
**Run flow:**

1. Drop raw JSON into `s3://raw/...` on MinIO.
2. DuckDB reads → writes Parquet to `bronze/` then `silver/`.
3. NLP/IE as Python tasks. Write chunks to `silver_chunks/`.
4. Embed → upsert to Qdrant. Entities/edges → Neo4j.
5. Hybrid retrieval API as a local FastAPI.\
   **Fixtures:** a handful of Notion and GitHub payloads in `tests/fixtures`.\
   **Gotchas:** constrain batch size; avoid Spark on day one; deterministic chunking.

---

## 2) Streaming-First (Kappa)

**Core stack:** Redpanda (Kafka-compatible), ksqlDB or Flink standalone, MinIO, Ray local for heavy NLP, Qdrant, Neo4j.\
**Run flow:**

1. Webhook handler writes to `topic.raw.*`.
2. ksqlDB/Flink parses → `topic.normalized.*`.
3. Ray workers subscribe for NER/relations → publish `topic.enriched.*`.
4. Sinks upsert to Qdrant and Neo4j.\
   **Fixtures:** load JSON events with `kcat` to topics.\
   **Gotchas:** keep exactly-once simple: idempotent upserts keyed by `content_hash`. Use compacted topics for dedupe.

---

## 3) Event-Driven Microservices + Lakehouse

**Core stack:** Services as small FastAPI apps, Redpanda, Postgres per service, Debezium outbox relays, MinIO, Qdrant, Neo4j.\
**Run flow:**

1. Each service writes business change + outbox in one transaction.
2. Debezium CDC publishes outbox→`events.*`.
3. Downstream services consume and write to MinIO/DBs.
4. A thin “indexer” service updates Qdrant and Neo4j.\
   **Fixtures:** spin only 2–3 services first: `ingest`, `normalize`, `indexer`.\
   **Gotchas:** resist over-splitting. Add tracing with OpenTelemetry locally.

---

## 4) Serverless Minimal (local)

**Core stack:** LocalStack (S3, SQS), AWS SAM/Serverless Offline or Google Workflows emulator, Prefect for sequencing, Qdrant, Neo4j.\
**Run flow:**

1. Webhook → local function (SAM/Serverless Offline) → S3 (LocalStack) + SQS.
2. Prefect flow polls SQS, runs normalization and embeddings, writes outputs.
3. Upsert to vector and graph.\
   **Fixtures:** trigger functions via HTTP; enqueue test SQS messages.\
   **Gotchas:** emulators differ from cloud. Keep IAM simple. Avoid Step Functions emulator unless needed.

---

## 5) Graph-First Core + Derived Embeddings

**Core stack:** Neo4j Desktop, MinIO, DuckDB, Qdrant. SHACL via pySHACL.\
**Run flow:**

1. Normalize to canonical CSV/Parquet for nodes and edges.
2. Load into Neo4j with `neo4j-admin database import` or APOC CSV.
3. Run SHACL/rules. Fix violations.
4. Generate graph embeddings (node2vec) and text embeddings. Concatenate or store separate.
5. Upsert to Qdrant with `ontology_version` tags.\
   **Fixtures:** a tiny ontology v0 with two entity types and two relations.\
   **Gotchas:** lock IDs early. Keep migration scripts versioned. Validate with SHACL on every run.

Note: MinIO serves as the raw object store. It captures original webhook payloads and normalized CSV/Parquet files before loading into Neo4j. This allows replay, audit, and deterministic reprocessing when ontology versions evolve or embedding models change.

---

## Minimum viable Compose file (components)

- `minio`, `qdrant`, `neo4j`, `redpanda` (only if streaming), `postgres` (only if microservices), `api` (FastAPI), `worker` (Ray/Prefect).\
  Add services incrementally per pattern.

## Local DX tips

- Seed command: `make seed` loads fixtures to MinIO and topics.
- Determinism: pin model versions and chunking params.
- Observability: OpenTelemetry collector + Grafana Tempo/Promtail/Loki all-in-one, optional.
- Test harness: golden answers for a few queries; assert retrieval precision over fixtures.

## Pros and Cons

Context: This data pipeline will be used to maintain vector embeddings and knowledge graph for a knowledge management system used in software product development. Sources of data will ultimately include document stores (Google, GitHub), Wiki pages (Notion, Confluence), messaging services (Slack), project management services (Linear), logs, observability platforms, and design services (Figma). The knowledge graph will maintain entities and relationships for the domain that the software solution addresses. It might also include entities and relationships that are common to software development (e.g. requirements, business rules, test cases). Within this context analyze and report on the pros and cons of each proposed data pipeline architecture.

Short answer: all five work, but trade-offs shift in your context: many SaaS sources, strong provenance, hybrid retrieval (vector + graph), and evolving ontologies.

## 1) Lakehouse + Batch

**Pros**

- Handles large backfills from Google Drive, GitHub history, Confluence exports, Slack exports.
- Strong provenance and reproducibility for audits and legal holds.
- Cheap compute with DuckDB/Trino; predictable costs.
- Easy quality gates (contracts, PII redaction) before embedding/graph writes.

**Cons**

- Latency is hours-to-day unless tuned; slower for Slack/Linear freshness.
- More ops around scheduling, compaction, and re-embeds.

**Fit**

- Excellent as the authoritative backbone for historical corpora and reprocessing when models or ontology change.

## 2) Streaming-First (Kappa)

**Pros**

- Near-real-time updates from webhooks: Notion, Slack events, Linear, GitHub pushes.
- Built-in replay via the log; smooth incremental upserts to vector DB and graph.
- Good for “what changed since last hour?” workflows.

**Cons**

- Highest operational complexity: exactly-once, idempotency, DLQs, schema evolution in topics.
- Text-heavy enrichment (NER, linking) can stall streams without careful async fan-out.

**Fit**

- Ideal for freshness-sensitive sources (Slack threads, ticket state, PRs) where minutes matter.

## 3) Event-Driven Microservices + Lakehouse

**Pros**

- Clear domain boundaries: “documents,” “code,” “design,” “tickets,” “observability.”
- Outbox + CDC gives reliable publish and auditability.
- Teams can evolve extractors independently; contracts per domain.

**Cons**

- More services than you need early. Governance and cross-service debugging are non-trivial.
- Versioning embeddings and ontology across services adds coordination overhead.

**Fit**

- Good when multiple teams will own different source domains and you expect rapid parallel evolution.

## 4) Serverless Minimal

**Pros**

- Fastest to ship a working prototype. Scales to spiky webhook bursts.
- Low infra to manage; pay per use. Easy to bolt on managed vector/graph.

**Cons**

- Orchestration limits for long-running NLP; cold starts.
- Harder local fidelity; emulators differ from cloud. Observability is weaker.

**Fit**

- Best for first working slice or low-volume tenants. Migrate hot paths later.

## 5) Graph-First Core + Derived Embeddings

**Pros**

- Strong semantic backbone for product/domain entities plus SDLC entities (requirements, rules, test cases, tickets, PRs, incidents).
- SHACL/rules catch integrity issues early; supports reasoning and higher-precision retrieval.
- Embeddings augmented with graph context improve answer quality and citation paths.

**Cons**

- Upfront ontology work and ongoing governance.
- Mapping messy SaaS payloads to canonical entities requires sustained effort.
- Performance tuning for hot nodes and traversal paths is non-trivial.

**Fit**

- Right when the KG is central to UX and explainability. Especially valuable for cross-system traces like “requirement → design → code → tests → deploy → incident.”

---

## Cross-context considerations

- **Identity resolution:** unify users across Slack/Google/GitHub/Linear. Required for permissions and provenance. Easier with Lakehouse backbone; harder if stream-only.
- **ACLs and tenancy:** per-doc and per-edge access control. Lakehouse and Graph-First handle audits best. Streaming needs careful sink filters.
- **Freshness SLOs:** Slack/Linear/GitHub need minutes; Drive/Confluence/Figma can be batch. Suggest dual path: stream for deltas, batch for backfills.
- **Model churn:** frequent re-embeds after chunking/LLM changes. Lakehouse simplifies replays; stream-only makes global re-runs painful.
- **Cost control:** batch modes for heavy IE; stream fan-out only for changed content.

---

## Practical selections by goal

- **Authoritative history + cheap reprocessing:** **Lakehouse + Batch** as core.
- **Live updates for user-facing KM:** **Streaming-First** for Slack/Linear/GitHub events feeding the same sinks.
- **Org with many owners:** **Event-Driven** when different teams own sources and contracts.
- **Prototype now:** **Serverless** for a thin slice, then graduate to Lakehouse + Streaming.
- **Explainable, semantic UX:** **Graph-First** overlay once v1 ontology stabilizes.

---

## Recommended path for your system

- **Phase 1:** Lakehouse backbone for all sources; Graph-First for SDLC + domain entities; embeddings derived from text + graph. Nightly batches + hourly mini-batches.
- **Phase 2:** Add Streaming for Slack, Linear, GitHub to reach sub-10-minute freshness; keep Lakehouse for replay and global re-embeds.
- **Phase 3:** If teams split, introduce Event-Driven boundaries with outbox/CDC. Keep one retrieval API that does hybrid search and graph hops.

**Risks to watch**

- Ontology creep without versioning. Mitigate with `ontology_version` tags on nodes, edges, and embeddings.
- Duplicate content across systems. Mitigate with content hashes and canonical doc IDs.
- Permission leaks. Mitigate with per-chunk ACLs propagated from sources and enforced at query time.

## Considerations for RAG and GraphRAG

### Architecture impacts

**1) Lakehouse + Batch**

- **Pros for RAG/GraphRAG:** cheap global re-embeds after chunking/model changes; strong provenance for citations; easy offline graph rewrites and negative sampling for retriever training.
- **Cons:** slower freshness for user-facing RAG; delayed entity linking means stale graph walks.

**2) Streaming-First (Kappa)**

- **Pros:** near-real-time chunk upserts, entity/edge deltas, and small-batch re-embeds; good for “answer with latest Slack/PR” prompts.
- **Cons:** heavy IE in-stream hurts tail latency; harder to run global re-embeds or graph refactors; permission propagation in-stream is complex.

**3) Event-Driven Microservices + Lakehouse**

- **Pros:** clear owners for retriever, chunker, linker, and graph-writer; outbox/CDC gives reliable citation lineage; can dual-write to old/new indexes during retriever upgrades.
- **Cons:** coordination tax across services for ontology and embedding version bumps; query-time hybrid (BM25+vec+graph) spans many services.

**4) Serverless Minimal**

- **Pros:** fast to stand up a working RAG with managed vector/graph; easy to prototype GraphRAG walks as functions.
- **Cons:** cold starts and limits hurt multi-hop GraphRAG; batch IE often exceeds function timeouts; local fidelity weak for relevance tuning.

**5) Graph-First Core + Derived Embeddings**

- **Pros:** best for GraphRAG quality, schema-aware chunking, and constrained traversals; SHACL/rules reduce hallucinations by pruning invalid paths; graph features boost rerankers.
- **Cons:** upfront ontology work; re-shaping the graph for retriever changes is slower; hot-spot nodes require careful indexing to keep walks fast.

### Cross-cutting requirements for high-quality RAG/GraphRAG

- **Provenance-by-chunk:** store source\_id, span offsets, commit/page IDs, and permissions on each chunk and edge; return citations deterministically.
- **Permission-aware retrieval:** filter at retrieval time, not just at index time; test for overexposure.
- **Hybrid retrieval:** BM25 + dense + graph walks with learned fusion; keep feature logs for offline tuning.
- **Chunking strategy:** structure-aware chunking (headings, code blocks, ticket threads) plus entity anchors for graph joins.
- **Versioning:** tag everything with `ontology_version`, `embed_model`, `chunker_version`; support dual indexes during upgrades.
- **Freshness tiers:** stream deltas for Slack/Linear/PRs; batch the rest; periodic mini-re-embeds for hot content.
- **Feedback loop:** capture click/accept/skip to improve rerankers; keep hard negatives from graph-adjacent but irrelevant chunks.
- **Eval harness:** task-focused eval sets (answerable with and without graph context) to quantify GraphRAG lift.

## Decision

### Factors

1. Avoid unnecessary implementation overhead and operational complexities early in the project.
2. Since we're at the intersection of research and development for a complex, multi-part system, the ability to rapidly prototype is a high priority.
3. Empowering experimentation is vital.
4. Must be able to run a prototype on a local machine.
5. Latency of up to an hour is acceptable. We do not need near-real-time updates.
6. Bear in mind the cost of heavy information extraction (named entity recognition, coreference resolution, entity resolution across sources, relation extraction, entity linking)
7. Observability is a core need for both prototyping and production

### Architecture Evaluation

- ✅ Lakehouse + Batch
  - a solid option for experimentation, research, and prototyping. Immutable data layers and deterministic transformations (via versioning) allow consistent comparisons across iterations, enabling us  to test different models, ontologies, and extraction configurations while maintaining traceability and rollback capability. 
- ❌ Streaming-First
  - too much operational complexity
- ❌ Event-Driven Microservices + Lakehouse
  - too much operational complexity and implementation overhead
- ❌ Serverless Minimal
  - &#x20;emulators differ from cloud, reducing local fidelity. 
  - observability is weaker for serverless: fragmented logs and traces make end-to-end correlation difficult.
- 2️⃣ Graph-First Core + Derived Embeddings
  - Potentially strongest for semantic correctness and utility, but requires upfront ontology definitions
  - Consider adding this to Lakehouse later

### Adding Graph-First to Lakehouse

Use a **Lakehouse backbone** for durability and reprocessing, with a **Graph-First semantic core** on top. Batch rules handle scale and governance. The graph powers reasoning and retrieval quality.

#### Design

- **Zones:** `raw` (immutable bytes) → `bronze` (normalized) → `silver` (validated) → `gold` (curated, entity/edge tables).
- **Ontology-first mapping:** source → canonical entities/relations; enforce SHACL; version with `ontology_version`.
- **Dual embeddings:** text chunks → `embed_text`; graph nodes/paths → `embed_graph`; fuse at query or store as separate collections.
- **Hybrid retrieval:** BM25 + vector + graph hops with learned fusion and permission filtering.
- **Mini-batch freshness:** hourly deltas for Slack/Linear/GitHub; nightly global compaction and quality checks.

#### End-to-end flow

1. **Ingest:** webhooks → queue → write raw to object store with provenance.
2. **Normalize:** map to canonical tables; validate against JSON Schema; compute `content_hash`.
3. **Entity/Relation extraction:** run NER/coref/linking; write candidate tables with confidence.
4. **Entity resolution:** deterministic rules + similarity; assign stable `entity_id`.
5. **Graph upsert:** write nodes/edges to Neo4j/GraphDB; run SHACL; quarantine violations.
6. **Chunk + embed:** structure-aware chunking; generate `embed_text`; compute `embed_graph` (node2vec/GraphSAGE) for changed subgraphs.
7. **Index:** upsert to vector DB with `{source_id, entity_id, acl, ontology_version, embed_model}`.
8. **Serve:** single API that fans to keyword, vector, and graph; merges results with citations and ACLs.

#### Ops and governance

- **Replays:** lakehouse is the source of truth for global re-embeds and ontology migrations.
- **Quality gates:** expectation suites at silver/gold; graph integrity checks on each commit.
- **Versioning:** dual-write to old/new indexes during retriever or ontology upgrades; cut over by tag.
- **ACLs:** propagate permissions at chunk and edge level; enforce at retrieval time.
- **Cost control:** run heavy IE in batch; keep streaming to metadata and changed documents only.

#### Minimal stack

- **Storage:** MinIO + Parquet/Delta.
- **Compute:** DuckDB/Polars for transform; Prefect/Dagster for orchestration.
- **Graph:** Neo4j + pySHACL.
- **Vector:** Qdrant/pgvector.
- **API:** FastAPI hybrid retriever.
- **Obs:** OpenTelemetry + Loki/Tempo; data lineage in the orchestrator.

#### Rollout

- **Phase 1:** Batch only. Build ontology v1. Populate graph from historical sources. Text embeddings only.
- **Phase 2:** Add graph embeddings for high-value types. Introduce mini-batches for hot sources.
- **Phase 3:** Learned fusion, feedback loop, and scheduled ontology releases with automated dual-indexing.

If you want me to emoji-ify content, specify the text or say “update the canvas” and which section.
