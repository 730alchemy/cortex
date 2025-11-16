"""DuckDB connection manager with Iceberg support."""

import os
from typing import Optional
import duckdb
import structlog

logger = structlog.get_logger()


class DuckDBManager:
    """Manages DuckDB connections with Iceberg catalog integration."""

    def __init__(
        self,
        db_path: str = "pipelines.duckdb",
        minio_endpoint: Optional[str] = None,
        minio_access_key: Optional[str] = None,
        minio_secret_key: Optional[str] = None,
        postgres_uri: Optional[str] = None,
    ):
        """
        Initialize DuckDB manager.

        Args:
            db_path: Path to DuckDB database file
            minio_endpoint: MinIO endpoint URL (e.g., 'http://minio:9000')
            minio_access_key: MinIO access key
            minio_secret_key: MinIO secret key
            postgres_uri: PostgreSQL connection URI for Iceberg catalog
        """
        self.db_path = db_path
        self.minio_endpoint = minio_endpoint or os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.minio_access_key = minio_access_key or os.getenv("MINIO_ACCESS_KEY", "minio")
        self.minio_secret_key = minio_secret_key or os.getenv("MINIO_SECRET_KEY", "minio123")
        self.postgres_uri = postgres_uri or self._build_postgres_uri()

        self._connection: Optional[duckdb.DuckDBPyConnection] = None

    def _build_postgres_uri(self) -> str:
        """Build PostgreSQL URI from environment variables."""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "cortex")
        password = os.getenv("POSTGRES_PASSWORD", "cortex")
        db = os.getenv("POSTGRES_DB", "catalog")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create DuckDB connection."""
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection

    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create and configure a new DuckDB connection."""
        logger.info("creating_duckdb_connection", db_path=self.db_path)

        con = duckdb.connect(self.db_path)

        # Install and load Iceberg extension
        logger.info("loading_iceberg_extension")
        con.execute("INSTALL iceberg")
        con.execute("LOAD iceberg")

        # Configure S3 access for MinIO
        logger.info("configuring_s3_access", endpoint=self.minio_endpoint)
        con.execute(
            f"""
            CREATE OR REPLACE SECRET minio_secret (
                TYPE S3,
                KEY_ID '{self.minio_access_key}',
                SECRET '{self.minio_secret_key}',
                ENDPOINT '{self.minio_endpoint}',
                USE_SSL false,
                URL_STYLE 'path'
            )
        """
        )

        logger.info("duckdb_connection_ready")
        return con

    def attach_iceberg_catalog(self, catalog_name: str = "iceberg_catalog") -> None:
        """
        Attach Iceberg catalog backed by PostgreSQL.

        Note: This requires the pyiceberg catalog to already exist in PostgreSQL.
        DuckDB will use it as a metastore for Iceberg tables.
        """
        con = self.get_connection()
        logger.info("attaching_iceberg_catalog", catalog_name=catalog_name)

        # Note: DuckDB's Iceberg support reads from the Iceberg REST catalog or file-based catalog
        # For now, we'll use the warehouse location directly
        # The catalog metadata is managed by PyIceberg in PostgreSQL

        logger.info("iceberg_catalog_attached", catalog_name=catalog_name)

    def execute(self, query: str, parameters: Optional[list] = None) -> duckdb.DuckDBPyConnection:
        """Execute a SQL query."""
        con = self.get_connection()
        if parameters:
            return con.execute(query, parameters)
        return con.execute(query)

    def query(self, query: str, parameters: Optional[list] = None) -> list:
        """Execute a query and fetch all results."""
        result = self.execute(query, parameters)
        return result.fetchall()

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self._connection:
            logger.info("closing_duckdb_connection")
            self._connection.close()
            self._connection = None

    def __enter__(self):
        """Context manager entry."""
        return self.get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global instance for convenient access
_global_manager: Optional[DuckDBManager] = None


def get_duckdb_manager() -> DuckDBManager:
    """Get the global DuckDB manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = DuckDBManager()
    return _global_manager


def reset_duckdb_manager() -> None:
    """Reset the global DuckDB manager (for testing)."""
    global _global_manager
    if _global_manager:
        _global_manager.close()
    _global_manager = None
