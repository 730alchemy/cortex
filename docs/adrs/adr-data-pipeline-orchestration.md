# ADR: Data Pipeline Orchestration

## Architectural Question
How should we orchestrate a multi-source data ingestion and transformation platform that ingests documents and events from numerous sources, stores versioned raw data, generates embeddings, performs information extraction, and maintains an evolving knowledge graph? Specifically: Prefect (task-oriented) or Dagster (asset-oriented)?

## Context and Constraints
- Sources include Notion, Slack, Linear, Google Docs, log streams, and incident reports.
- All incoming documents require versioned storage (MinIO for now, S3-compliant source probably)
- Downstream transformations include chunking, embedding, and vector database persistence.
- Additional processing includes information extraction (NER, RE) with evolving models.
- Extracted entities and relations feed a knowledge graph; ontology will evolve continuously.
- The platform must support experimentation: comparing embedding models, chunking strategies, extraction models, and schema versions over the same stable corpus.
- The system must support reprocessing, backfilling, and tracking data states.
- MLflow integration may be used to analyze experimental runs.

## Decision
We choose **Dagster** as the workflow orchestrator.

## Rationale
### 1. Asset-Oriented Model
Dagster’s asset abstraction mirrors the data structure of the system: raw documents, canonical documents, chunks, embeddings, extracted facts, entity sets, and knowledge graph projections. This structured representation is core to the platform.

### 2. Partitioning for Experimentation
The need to compare:
- multiple embedding models,
- multiple chunking strategies,
- multiple information extraction models,
- multiple knowledge graph schema versions,
requires multi-dimensional partitioning. Dagster partitions natively express this experimental grid.

### 3. Lineage and Reproducibility
Dagster provides first-class lineage across assets. Every materialization carries metadata including content hash, raw object reference, model version, schema version, and upstream dependencies. This enables reproducible analyses and debugging.

### 4. Backfills and Schema Evolution
Dagster’s partition materialization and backfill infrastructure supports reprocessing when:
- raw documents change,
- embedding models are upgraded,
- extraction models improve,
- knowledge graph schema updates occur.
Prefect offers no native representation for these relationships.

### 5. Integration with an Evolving Knowledge Graph
An evolving ontology requires rebuilding derived assets consistently. Dagster treats schema version changes as new partitions, enabling safe recomputation across the corpus.

### 6. Aligns with Iceberg Integration
Iceberg will serve as the data substrate for document metadata, extracted facts, chunk information, and experiment traces. Dagster complements Iceberg by orchestrating how data flows into and out of Iceberg tables.

### 7. Prefect Is Not a Good Fit for Systematic Experiments
Prefect is effective for straightforward webhook-driven flows. However, it lacks built-in constructs for representing the experimental search space or asset version matrices. Adding these would require substantial custom metadata management.

## Alternatives Considered
### Prefect
A task-oriented orchestrator that:
- Works well with webhook triggers.
- Offers simplicity and low initial overhead.
- Would require significant custom engineering for lineage, version tracking, systematic experimentation, and multi-model asset matrices.

## Implications
- The system will be structured explicitly around assets, metadata, and partitions.
- Experimentation across models, chunking strategies, schemas will be expressed through Dagster’s partitioning and backfill capabilities.
- Iceberg tables will be the primary analytical store and artifact registry, with Dagster orchestrating updates to them.
- The platform will have a more formal pipeline structure and higher initial complexity but significantly lower long-term complexity.
- Prefect’s simplicity and webhook ergonomics will be sacrificed in favor of structured data governance and scalable computational experimentation.

