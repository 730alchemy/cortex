from datetime import datetime
from typing import cast

import dagster as dg

from .resources import MinIOResource
from .types import FileHashList


@dg.asset(  # pyright: ignore[reportUnknownMemberType]
    config_schema={"new_files": dg.Field(list, default_value=[])}
)
def assetsRaw(
    context: dg.AssetExecutionContext, minio: MinIOResource
) -> dg.MaterializeResult[dg.Any]:
    """
    Asset that processes new or modified files detected by the sensor.

    Receives list of files with their content hashes.
    Each file is: {'path': str, 'hash': str}
    """
    new_files = cast(FileHashList, context.op_config.get("new_files", []))  # pyright: ignore[reportAny]
    bucket = "datalake-dev-raw"

    context.log.info(
        f"Materializing assetsRaw with {len(new_files)} new/modified file(s)"
    )

    # Process each new file
    processed_files: list[str] = []
    processed_hashes: list[str] = []

    for file_info in new_files:
        file_path = file_info["path"]
        file_hash = file_info["hash"]
        context.log.info(f"Processing file: {file_path} (hash: {file_hash[:12]}...)")

        timestamp = datetime.now().strftime("%Y%m%d")
        key = f"source=folder/ingest_date={timestamp}/hash={file_hash}"
        minio.upload_file(file_path, bucket, key)

        processed_files.append(file_path)
        if file_hash:
            processed_hashes.append(file_hash)

    # Return materialization result with metadata
    return dg.MaterializeResult(
        metadata={
            "processed_file_count": len(processed_files),
            "processed_hashes": dg.MetadataValue.json(processed_hashes),
            "file_paths": dg.MetadataValue.json(processed_files),
        }
    )


@dg.asset  # pyright: ignore[reportUnknownMemberType]
def assetsCanonical() -> dg.MaterializeResult[dg.Any]: ...


@dg.asset  # pyright: ignore[reportUnknownMemberType]
def assetsChunks() -> dg.MaterializeResult[dg.Any]: ...


@dg.asset  # pyright: ignore[reportUnknownMemberType]
def assetsEmbeddings() -> dg.MaterializeResult[dg.Any]: ...
