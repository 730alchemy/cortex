"""Dagster definitions - central registry for assets, jobs, sensors, and resources."""

from pathlib import Path
from dagster import load_from_defs_folder, definitions, Definitions, load_assets_from_modules
import structlog

from orchestration import assets, sensors
from orchestration.resources import MinIOResource, DuckDBResource

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

# Load all assets
all_assets = load_assets_from_modules([assets])

# Load all sensors
all_sensors = [
    sensors.file_drop_sensor,
]

# Define resources
resources = {
    "minio": MinIOResource(
        endpoint_url="http://minio:9000",  # Docker internal network
        access_key="minio",
        secret_key="minio123",
        data_lake_bucket="data-lake",
        warehouse_bucket="warehouse",
    ),
    "duckdb": DuckDBResource(
        db_path="/opt/dagster/dagster_home/pipelines.duckdb",
        minio_endpoint="http://minio:9000",
        minio_access_key="minio",
        minio_secret_key="minio123",
    ),
}

@definitions
def defs():
    return load_from_defs_folder(path_within_project=Path(__file__).parent)

# Create definitions
#defs = Definitions(
#    assets=all_assets,
#    sensors=all_sensors,
#    resources=resources,
#)
