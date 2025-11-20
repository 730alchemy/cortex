from datetime import datetime

import dagster as dg

from .resources import MinIOResource


@dg.asset
def assetsR(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...


@dg.asset(config_schema={"new_files": dg.Field(list, default_value=[])})
def assetsRaw(
    context: dg.AssetExecutionContext, minio: MinIOResource
) -> dg.MaterializeResult:
    """
    Asset that processes new or modified files detected by the sensor.

    Receives list of files with their content hashes.
    Each file is: {'path': str, 'hash': str}
    """
    new_files = context.op_config.get("new_files", [])
    bucket = "datalake-dev-raw"

    context.log.info(
        f"Materializing assetsRaw with {len(new_files)} new/modified file(s)"
    )

    # Process each new file
    processed_files = []
    processed_hashes = []

    for file_info in new_files:
        if isinstance(file_info, dict):
            file_path = file_info["path"]
            file_hash = file_info["hash"]
            context.log.info(
                f"Processing file: {file_path} (hash: {file_hash[:12]}...)"
            )
        else:
            context.log.error("file_info has the wrong format")
            break

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


@dg.asset
def assetsCanonical(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...


@dg.asset
def assetsChunks(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...


@dg.asset
def assetsEmbeddings(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...
