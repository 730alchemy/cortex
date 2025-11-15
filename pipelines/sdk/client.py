"""Data access SDK for querying pipeline outputs."""

from typing import Iterator, Optional, Dict, Any, List
from datetime import datetime
import boto3
import structlog

from catalog.iceberg_catalog import get_iceberg_catalog_manager
from catalog.duckdb_manager import get_duckdb_manager

logger = structlog.get_logger()


class PipelineClient:
    """Client for accessing pipeline data via Iceberg tables and MinIO."""

    def __init__(
        self,
        minio_endpoint: str = "http://localhost:9000",
        minio_access_key: str = "minio",
        minio_secret_key: str = "minio123",
        data_lake_bucket: str = "data-lake",
    ):
        """
        Initialize pipeline client.

        Args:
            minio_endpoint: MinIO endpoint URL
            minio_access_key: MinIO access key
            minio_secret_key: MinIO secret key
            data_lake_bucket: Bucket name for raw data
        """
        self.minio_endpoint = minio_endpoint
        self.data_lake_bucket = data_lake_bucket

        # S3 client for blob access
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=minio_endpoint,
            aws_access_key_id=minio_access_key,
            aws_secret_access_key=minio_secret_key,
        )

        # Iceberg catalog manager
        self.catalog_manager = get_iceberg_catalog_manager()

        # DuckDB manager
        self.duckdb_manager = get_duckdb_manager()

    def get_doc(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata by doc_id.

        Args:
            doc_id: Document ID (SHA256 hash)

        Returns:
            Document metadata dict or None if not found
        """
        logger.info("getting_doc", doc_id=doc_id[:16])

        # Query via DuckDB (faster than PyIceberg scan)
        con = self.duckdb_manager.get_connection()

        # Use Iceberg scan via DuckDB
        result = con.execute(
            """
            SELECT doc_id, source_id, mime, size_bytes,
                   ingest_first_at, ingest_last_at,
                   url, license, hash_alg, dq_status
            FROM iceberg_scan('s3://warehouse/catalog/docs')
            WHERE doc_id = ?
            LIMIT 1
        """,
            [doc_id],
        ).fetchone()

        if not result:
            return None

        # Convert to dict
        columns = [
            "doc_id",
            "source_id",
            "mime",
            "size_bytes",
            "ingest_first_at",
            "ingest_last_at",
            "url",
            "license",
            "hash_alg",
            "dq_status",
        ]
        return dict(zip(columns, result))

    def iter_docs(
        self,
        source_id: Optional[str] = None,
        mime_type: Optional[str] = None,
        ingest_after: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate over documents with optional filters.

        Args:
            source_id: Filter by source_id (supports LIKE pattern)
            mime_type: Filter by MIME type
            ingest_after: Only docs ingested after this timestamp
            limit: Maximum number of documents to return

        Yields:
            Document metadata dicts
        """
        logger.info("iterating_docs", source_id=source_id, mime_type=mime_type, limit=limit)

        # Build query
        query = "SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs') WHERE 1=1"
        params = []

        if source_id:
            if "%" in source_id or "_" in source_id:
                query += " AND source_id LIKE ?"
            else:
                query += " AND source_id = ?"
            params.append(source_id)

        if mime_type:
            query += " AND mime = ?"
            params.append(mime_type)

        if ingest_after:
            query += " AND ingest_first_at > ?"
            params.append(ingest_after)

        query += " ORDER BY ingest_first_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        # Execute query
        con = self.duckdb_manager.get_connection()
        result = con.execute(query, params)

        # Yield rows as dicts
        columns = [desc[0] for desc in result.description]
        for row in result.fetchall():
            yield dict(zip(columns, row))

    def open_blob(self, doc_id: str) -> bytes:
        """
        Retrieve raw document content from MinIO.

        Args:
            doc_id: Document ID (SHA256 hash)

        Returns:
            Raw document bytes

        Raises:
            FileNotFoundError: If document not found in storage
        """
        logger.info("opening_blob", doc_id=doc_id[:16])

        # Get doc metadata to find storage location
        doc = self.get_doc(doc_id)
        if not doc:
            raise FileNotFoundError(f"Document not found: {doc_id}")

        # Try to find blob in MinIO by listing objects
        # Storage pattern: raw/source=.../ingest_date=.../run_id=.../sha256=<doc_id>/blob.bin
        prefix = f"raw/"

        try:
            # List objects to find the blob
            response = self.s3_client.list_objects_v2(
                Bucket=self.data_lake_bucket,
                Prefix=prefix,
            )

            # Find object matching doc_id
            for obj in response.get("Contents", []):
                if f"sha256={doc_id}" in obj["Key"] and obj["Key"].endswith("blob.bin"):
                    # Download the blob
                    logger.info("downloading_blob", key=obj["Key"])
                    response = self.s3_client.get_object(
                        Bucket=self.data_lake_bucket, Key=obj["Key"]
                    )
                    return response["Body"].read()

            raise FileNotFoundError(f"Blob not found in storage for doc_id: {doc_id}")

        except Exception as e:
            logger.error("blob_download_failed", doc_id=doc_id, error=str(e))
            raise

    def query(self, sql: str, parameters: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Execute arbitrary SQL query via DuckDB.

        Args:
            sql: SQL query string
            parameters: Query parameters for placeholders

        Returns:
            List of result dicts
        """
        logger.info("executing_query", sql=sql[:100])

        con = self.duckdb_manager.get_connection()
        result = con.execute(sql, parameters or [])

        columns = [desc[0] for desc in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.

        Returns:
            Dict with document counts, sizes, etc.
        """
        logger.info("getting_stats")

        con = self.duckdb_manager.get_connection()

        stats = {}

        # Total documents
        result = con.execute(
            """
            SELECT COUNT(*) as count,
                   SUM(size_bytes) as total_bytes,
                   MIN(ingest_first_at) as earliest_ingest,
                   MAX(ingest_last_at) as latest_ingest
            FROM iceberg_scan('s3://warehouse/catalog/docs')
        """
        ).fetchone()

        stats["total_docs"] = result[0]
        stats["total_bytes"] = result[1]
        stats["earliest_ingest"] = result[2]
        stats["latest_ingest"] = result[3]

        # By source
        result = con.execute(
            """
            SELECT source_id, COUNT(*) as count
            FROM iceberg_scan('s3://warehouse/catalog/docs')
            GROUP BY source_id
            ORDER BY count DESC
        """
        ).fetchall()

        stats["by_source"] = {row[0]: row[1] for row in result}

        # By MIME type
        result = con.execute(
            """
            SELECT mime, COUNT(*) as count
            FROM iceberg_scan('s3://warehouse/catalog/docs')
            GROUP BY mime
            ORDER BY count DESC
        """
        ).fetchall()

        stats["by_mime"] = {row[0]: row[1] for row in result}

        return stats
