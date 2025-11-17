import dagster as dg


@dg.asset
def assetsR(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

@dg.asset(config_schema={'new_files': dg.Field(list, default_value=[])})
def assetsRaw(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """
    Asset that processes new files detected by the sensor.

    Receives list of new file paths via config and processes them.
    """
    new_files = context.op_config.get('new_files', [])

    context.log.info(f'Materializing assetsRaw with {len(new_files)} new file(s)')

    # Process each new file
    processed_files = []
    for file_path in new_files:
        context.log.info(f'Processing file: {file_path}')
        # TODO: Add your file processing logic here
        # Example: read file, parse data, transform, etc.
        processed_files.append(file_path)

    # Return materialization result with metadata
    return dg.MaterializeResult(
        metadata={
            'processed_file_count': len(processed_files),
            'file_paths': dg.MetadataValue.json(processed_files)
        }
    )

@dg.asset
def assetsCanonical(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

@dg.asset
def assetsChunks(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

@dg.asset
def assetsEmbeddings(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...
