import hashlib
import os
from pathlib import Path

import dagster as dg

from .assets import assetsRaw


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


@dg.sensor(
    target=None,
    asset_selection=[assetsRaw],
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def sensors(context: dg.SensorEvaluationContext) -> dg.SensorResult:
    """
    Sensor that monitors a directory for new or modified files based on content hashing.

    Directory path is configured via INPUT_DIR environment variable.
    Uses SHA256 content hashing to detect new/modified files.
    Queries past asset materializations to determine which files have been processed.
    Only successfully materialized files are marked as "seen" (true idempotency).
    """
    # Get directory path from environment variable
    input_dir = os.environ.get("INPUT_DIR")

    if not input_dir:
        context.log.warning("INPUT_DIR environment variable not set")
        return dg.SkipReason("INPUT_DIR environment variable not configured")

    input_path = Path(input_dir)

    # Check if directory exists
    if not input_path.exists():
        context.log.warning(f"Directory does not exist: {input_path}")
        return dg.SkipReason(f"Directory does not exist: {input_path}")

    if not input_path.is_dir():
        context.log.error(f"Path is not a directory: {input_path}")
        return dg.SkipReason(f"Path is not a directory: {input_path}")

    # Get all files in directory and compute hashes
    current_file_hashes = {}  # {hash: path}
    try:
        for file_path in input_path.iterdir():
            if file_path.is_file():
                try:
                    file_hash = compute_file_hash(file_path)
                    current_file_hashes[file_hash] = str(file_path.absolute())
                except Exception as e:
                    context.log.error(f"Error hashing file {file_path}: {e}")
                    continue
    except Exception as e:
        context.log.error(f"Error reading directory {input_path}: {e}")
        return dg.SkipReason(f"Error reading directory: {e}")

    # Query past asset materializations to get seen hashes
    # This ensures only successfully processed files are considered "seen"
    seen_hashes = set()
    try:
        records = context.instance.get_event_records(
            event_records_filter=dg.EventRecordsFilter(
                event_type=dg.DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=dg.AssetKey(["assetsRaw"]),
            )
        )

        for record in records:
            materialization = record.asset_materialization
            if materialization and materialization.metadata:
                processed_hashes_meta = materialization.metadata.get("processed_hashes")
                if processed_hashes_meta:
                    # Extract the JSON list of hashes
                    processed_hashes = processed_hashes_meta.value
                    if isinstance(processed_hashes, list):
                        seen_hashes.update(processed_hashes)

        context.log.info(
            f"Found {len(seen_hashes)} previously processed file hash(es) from materialization history"
        )

    except Exception as e:
        context.log.error(f"Error querying materialization history: {e}")
        # Continue with empty seen_hashes on error

    # Identify new/modified files by comparing hashes only
    current_hashes = set(current_file_hashes.keys())
    new_hashes = current_hashes - seen_hashes

    if not new_hashes:
        context.log.info(f"No new or modified files detected in {input_path}")
        return dg.SkipReason("No new or modified files detected")

    # Build list of new files with their hashes
    new_files_with_hashes = [
        {"path": current_file_hashes[h], "hash": h} for h in sorted(new_hashes)
    ]

    # Log new files found
    context.log.info(f"Detected {len(new_hashes)} new/modified file(s) in {input_path}")
    for item in new_files_with_hashes:
        context.log.info(
            f"  - {Path(item['path']).name} (hash: {item['hash'][:12]}...)"
        )

    # Trigger asset materialization with new file info
    return dg.RunRequest(
        run_config={
            "ops": {"assetsRaw": {"config": {"new_files": new_files_with_hashes}}}
        },
        tags={
            "new_file_count": str(len(new_hashes)),
            "input_directory": str(input_path),
        },
    )
