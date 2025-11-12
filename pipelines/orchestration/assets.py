"""Dagster assets for data pipeline ingestion."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from dagster import asset, AssetExecutionContext
import structlog

from connectors.file_drop import FileDropConnector
from orchestration.resources import MinIOResource, DuckDBResource

logger = structlog.get_logger()


@asset(
    description="Ingest files from file drop directory into raw object store and catalog",
    compute_kind="python",
)
def ingest_file_drop(
    context: AssetExecutionContext,
    minio: MinIOResource,
    duckdb: DuckDBResource,
) -> Dict[str, Any]:
    """
    Ingest files from the file drop connector.

    This asset:
    1. Scans the watch directory for files
    2. Computes content-addressable doc_id (SHA256)
    3. Checks if already ingested
    4. Stores raw file in MinIO
    5. Writes metadata to catalog via DuckDB
    6. Records lineage event
    """
    # Get run ID
    run_id = context.run.run_id

    # Initialize connector
    watch_dir = Path("samples/watch/file_drop")
    connector = FileDropConnector(
        watch_directory=watch_dir,
        source_name="file_drop",
        recursive=False,
    )

    # Get DuckDB connection
    con = duckdb.get_manager().get_connection()

    # Track stats
    stats = {
        "discovered": 0,
        "ingested": 0,
        "skipped": 0,
        "errors": 0,
        "run_id": run_id,
    }

    for item in connector.fetch_all():
        stats["discovered"] += 1

        try:
            # Compute doc_id from content
            doc_id = connector.compute_doc_id(item.content)

            context.log.info(
                f"Processing: {item.source_id} -> doc_id: {doc_id[:16]}..."
            )

            # Check if doc already exists in catalog
            existing_docs = con.execute(
                "SELECT doc_id FROM iceberg_catalog.docs WHERE doc_id = ?",
                [doc_id]
            ).fetchall()

            now = datetime.utcnow()
            is_new = len(existing_docs) == 0

            if is_new:
                # New document - store in MinIO
                ingest_date = now.strftime("%Y-%m-%d")
                storage_key = (
                    f"raw/source=file_drop/ingest_date={ingest_date}/"
                    f"run_id={run_id}/sha256={doc_id}/blob.bin"
                )

                # Upload file content
                minio.upload_bytes(
                    content=item.content,
                    bucket=minio.data_lake_bucket,
                    key=storage_key,
                )

                # Upload manifest
                manifest = {
                    "source_id": item.source_id,
                    "doc_id": doc_id,
                    "mime": item.mime_type,
                    "size_bytes": item.size_bytes,
                    "fetched_at": item.fetched_at.isoformat() if item.fetched_at else now.isoformat(),
                    "url": item.url,
                    "etag": item.etag,
                    "license": item.license,
                    "checksum": doc_id,
                    "hash_alg": "sha256",
                    "metadata": item.metadata,
                }

                manifest_key = storage_key.replace("blob.bin", "manifest.json")
                minio.upload_bytes(
                    content=json.dumps(manifest, indent=2).encode(),
                    bucket=minio.data_lake_bucket,
                    key=manifest_key,
                )

                # Insert into docs table via DuckDB
                con.execute("""
                    INSERT INTO iceberg_catalog.docs
                    (doc_id, source_id, mime, size_bytes, ingest_first_at, ingest_last_at,
                     url, license, hash_alg, dq_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    doc_id,
                    item.source_id,
                    item.mime_type,
                    item.size_bytes,
                    now,
                    now,
                    item.url,
                    item.license,
                    "sha256",
                    "pending"
                ])

                context.log.info(f"✓ Ingested new document: {doc_id[:16]}...")
                stats["ingested"] += 1

            else:
                # Document exists - update last seen time
                con.execute("""
                    UPDATE iceberg_catalog.docs
                    SET ingest_last_at = ?
                    WHERE doc_id = ?
                """, [now, doc_id])

                context.log.info(f"⊙ Document already exists: {doc_id[:16]}...")
                stats["skipped"] += 1

            # Always record version (new or re-ingest)
            con.execute("""
                INSERT INTO iceberg_catalog.doc_versions
                (doc_id, run_id, source_id, ingest_at, etag)
                VALUES (?, ?, ?, ?, ?)
            """, [
                doc_id,
                run_id,
                item.source_id,
                now,
                item.etag
            ])

        except Exception as e:
            context.log.error(f"✗ Error processing {item.source_id}: {e}")
            stats["errors"] += 1
            continue

    context.log.info(
        f"Ingestion complete: {stats['ingested']} new, "
        f"{stats['skipped']} skipped, {stats['errors']} errors"
    )

    return stats
