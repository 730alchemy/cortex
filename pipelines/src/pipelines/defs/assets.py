import dagster as dg


@dg.asset
def assetsR(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...


@dg.asset(config_schema={"new_files": dg.Field(list, default_value=[])})
def assetsRaw(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """
    Asset that processes new or modified files detected by the sensor.

    Receives list of files with their content hashes.
    Each file is: {'path': str, 'hash': str}
    """
    new_files = context.op_config.get("new_files", [])

    context.log.info(
        f"Materializing assetsRaw with {len(new_files)} new/modified file(s)"
    )

    # Process each new file
    processed_files = []
    processed_hashes = []

    for file_info in new_files:
        # Handle both old format (string path) and new format (dict with path/hash)
        if isinstance(file_info, dict):
            file_path = file_info["path"]
            file_hash = file_info["hash"]
            context.log.info(
                f"Processing file: {file_path} (hash: {file_hash[:12]}...)"
            )
        else:
            # Backwards compatibility with old string format
            file_path = file_info
            file_hash = None
            context.log.info(f"Processing file: {file_path}")

        # TODO: Add your file processing logic here
        # Example: read file, parse data, transform, etc.
        # with open(file_path, 'r') as f:
        #     data = f.read()
        #     # process data...

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
