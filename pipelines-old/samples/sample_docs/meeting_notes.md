# Team Meeting Notes - Pipeline Design Session

**Date**: 2025-01-11
**Attendees**: Engineering Team
**Topic**: Data Pipeline Architecture

## Decisions Made

### 1. Architecture Pattern
**Decision**: Use Lakehouse + Graph-First architecture

**Rationale**:
- Batch processing acceptable (hourly updates)
- Local-first development important
- Strong provenance required for RAG citations
- Experimentation is a key requirement

**Alternatives Considered**:
- Streaming-first: Rejected due to operational complexity
- Serverless: Rejected due to local fidelity issues

### 2. Technology Selections

**Orchestration**: Dagster
- Asset-based model fits our use case
- Great local UI for development
- Built-in lineage tracking

**Storage**: MinIO + Apache Iceberg
- S3-compatible for cloud portability
- Iceberg provides time travel and schema evolution
- ACID transactions for metadata

**Query Engine**: DuckDB (not Spark)
- Zero JVM overhead
- Embedded in Dagster
- Native Iceberg support
- Perfect for batch workloads

**Graph DB**: Neo4j
- Strong community support
- Built-in vector search
- APOC procedures for utilities

**Vector DB**: Qdrant
- Open source
- Good Docker support
- Fast vector search

### 3. Data Model

**Content-Addressable Documents**:
- Use SHA256 hash as doc_id
- Enables automatic deduplication
- Stable identifiers for citations

**Partition Strategy**:
- Daily partitions by ingest_date
- Enables efficient time-range queries
- Simplifies data retention

**Versioning**:
- Separate doc_versions table
- Track every re-ingest
- Support reproducibility

## Action Items

- [x] Create docker-compose with all services
- [x] Implement file drop connector
- [x] Set up Iceberg catalog
- [x] Build Dagster assets and sensors
- [ ] Add text extraction
- [ ] Implement entity extraction
- [ ] Populate knowledge graph
- [ ] Build API gateway
- [ ] Integrate with TUI

## Open Questions

1. **Text Extraction**: Which library for PDF extraction?
   - Options: pdfminer, PyPDF2, unstructured
   - Need benchmarking

2. **Entity Resolution**: How to handle name variations?
   - May need fuzzy matching
   - Consider using embeddings for similarity

3. **Graph Schema**: Start with manual ontology or auto-discover?
   - Lean toward manual for core entities
   - Auto-discover for extensions

## Next Meeting

**Date**: TBD
**Topics**: Text extraction benchmarking, ontology design
