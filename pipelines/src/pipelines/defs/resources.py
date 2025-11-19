from dagster import ConfigurableResource, Definitions, definitions
import boto3
from pydantic import Field
import structlog
import os

logger = structlog.get_logger("dagster-resource")


class MinIOResource(ConfigurableResource):
    """MinIO S3-compatible storage resource."""

    endpoint_url: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    access_key: str = os.getenv("MINIO_ROOT_USER", "minioroot")
    secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "minioroot")
    data_lake_bucket: str = Field(default="undefined-data-lake")
    warehouse_bucket: str = Field(default="undefined-warehouse")

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
        client.close()

    def upload_bytes(self, content: bytes, bucket: str, key: str) -> None:
        """Upload bytes to MinIO."""
        client = self.get_client()
        client.put_object(Bucket=bucket, Key=key, Body=content)
        logger.info("bytes_uploaded", bucket=bucket, key=key, size=len(content))
        client.close()

    def download_bytes(self, bucket: str, key: str) -> bytes:
        """Download bytes from MinIO."""
        client = self.get_client()
        response = client.get_object(Bucket=bucket, Key=key)
        client.close()
        return response["Body"].read()


@definitions
def resources():
    return Definitions(
        resources={
            "minio": MinIOResource(),
        }
    )
