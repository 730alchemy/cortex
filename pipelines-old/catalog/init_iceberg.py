"""Initialize Iceberg catalog and create all tables using DuckDB."""

import structlog
from catalog.duckdb_manager import get_duckdb_manager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()


def main():
    """Initialize the Iceberg catalog with all required tables using DuckDB."""
    logger.info("starting_iceberg_initialization")

    try:
        # Get DuckDB manager
        duckdb_mgr = get_duckdb_manager()
        con = duckdb_mgr.get_connection()

        # Install and load Iceberg extension
        logger.info("loading_iceberg_extension")
        con.execute("INSTALL iceberg")
        con.execute("LOAD iceberg")

        # Create Iceberg catalog namespace
        logger.info("creating_namespace")
        con.execute("CREATE SCHEMA IF NOT EXISTS iceberg_catalog")

        # Create docs table
        logger.info("creating_docs_table")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS iceberg_catalog.docs (
                doc_id VARCHAR PRIMARY KEY,
                source_id VARCHAR NOT NULL,
                mime VARCHAR,
                size_bytes BIGINT,
                ingest_first_at TIMESTAMP NOT NULL,
                ingest_last_at TIMESTAMP NOT NULL,
                url VARCHAR,
                license VARCHAR,
                hash_alg VARCHAR DEFAULT 'sha256',
                dq_status VARCHAR DEFAULT 'pending'
            )
        """
        )

        # Create doc_versions table
        logger.info("creating_doc_versions_table")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS iceberg_catalog.doc_versions (
                doc_id VARCHAR NOT NULL,
                run_id VARCHAR NOT NULL,
                source_id VARCHAR NOT NULL,
                ingest_at TIMESTAMP NOT NULL,
                etag VARCHAR
            )
        """
        )

        # Create doc_text_pages table (for future text extraction)
        logger.info("creating_doc_text_pages_table")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS iceberg_catalog.doc_text_pages (
                doc_id VARCHAR NOT NULL,
                page_no INTEGER NOT NULL,
                lang VARCHAR,
                char_count INTEGER,
                has_ocr BOOLEAN,
                storage_path VARCHAR NOT NULL,
                extracted_at TIMESTAMP NOT NULL
            )
        """
        )

        # Create events_lineage table
        logger.info("creating_events_lineage_table")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS iceberg_catalog.events_lineage (
                event_id VARCHAR PRIMARY KEY,
                run_id VARCHAR NOT NULL,
                task_name VARCHAR NOT NULL,
                input_ids VARCHAR[],
                output_ids VARCHAR[],
                event_time TIMESTAMP NOT NULL,
                duration_ms BIGINT
            )
        """
        )

        # List tables to verify
        tables = con.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'iceberg_catalog'
            ORDER BY table_name
        """
        ).fetchall()

        table_names = [t[0] for t in tables]
        logger.info("initialization_complete", tables=table_names)

        print("\n✓ Iceberg catalog initialized successfully with DuckDB!")
        print(f"✓ Created {len(table_names)} tables: {', '.join(table_names)}")
        print("\nYou can now:")
        print("  1. Start the Dagster daemon to run sensors")
        print("  2. Drop files into samples/watch/file_drop/")
        print("  3. Query tables via DuckDB: make duckdb-shell")

    except Exception as e:
        logger.error("initialization_failed", error=str(e), exc_info=True)
        print(f"\n✗ Failed to initialize Iceberg catalog: {e}")
        raise


if __name__ == "__main__":
    main()
