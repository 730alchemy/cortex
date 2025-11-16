"""Dagster resources for pipeline components."""

import boto3
from dagster import ConfigurableResource
from pydantic import Field
import structlog

from catalog.duckdb_manager import DuckDBManager

logger = structlog.get_logger()


class MinIOResource(ConfigurableResource):
    """MinIO S3-compatible storage resource."""

    endpoint_url: str = Field(default="http://localhost:9000")
    access_key: str = Field(default="minio")
    secret_key: str = Field(default="minio123")
    data_lake_bucket: str = Field(default="data-lake")
    warehouse_bucket: str = Field(default="warehouse")

    def get_client(self):
        """Get boto3 S3 client configured for MinIO."""
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def upload_file(self, file_path: str, bucket: str, key: str) -> None:
        """Upload a file to MinIO."""
        client = self.get_client()
        client.upload_file(file_path, bucket, key)
        logger.info("file_uploaded", bucket=bucket, key=key)

    def upload_bytes(self, content: bytes, bucket: str, key: str) -> None:
        """Upload bytes to MinIO."""
        client = self.get_client()
        client.put_object(Bucket=bucket, Key=key, Body=content)
        logger.info("bytes_uploaded", bucket=bucket, key=key, size=len(content))

    def download_bytes(self, bucket: str, key: str) -> bytes:
        """Download bytes from MinIO."""
        client = self.get_client()
        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()


class DuckDBResource(ConfigurableResource):
    """DuckDB resource with Iceberg support."""

    db_path: str = Field(default="pipelines.duckdb")
    minio_endpoint: str = Field(default="http://localhost:9000")
    minio_access_key: str = Field(default="minio")
    minio_secret_key: str = Field(default="minio123")

    def get_manager(self) -> DuckDBManager:
        """Get DuckDB manager."""
        return DuckDBManager(
            db_path=self.db_path,
            minio_endpoint=self.minio_endpoint,
            minio_access_key=self.minio_access_key,
            minio_secret_key=self.minio_secret_key,
        )

    def execute(self, query: str, parameters=None):
        """Execute a query using DuckDB."""
        manager = self.get_manager()
        return manager.execute(query, parameters)

    def query(self, query: str, parameters=None):
        """Execute a query and return results."""
        manager = self.get_manager()
        return manager.query(query, parameters)
