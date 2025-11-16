"""Dagster sensors for continuous ingestion."""

import os
from pathlib import Path
from dagster import sensor, RunRequest, SkipReason, SensorEvaluationContext
import structlog

logger = structlog.get_logger()


@sensor(
    name="file_drop_sensor",
    description="Watches file drop directory and triggers ingestion when new files appear",
    minimum_interval_seconds=30,  # Check every 30 seconds
)
def file_drop_sensor(context: SensorEvaluationContext):
    """
    Sensor that monitors the file drop directory for new files.

    Triggers the ingest_file_drop asset when files are detected.
    """
    watch_dir = Path("samples/watch/file_drop")

    # Create directory if it doesn't exist
    watch_dir.mkdir(parents=True, exist_ok=True)

    # Scan for files
    files = [f for f in watch_dir.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not files:
        return SkipReason("No files found in watch directory")

    # Check cursor to see if we've already processed these files
    cursor_dict = context.cursor or {}
    cursor = eval(cursor_dict) if isinstance(cursor_dict, str) else cursor_dict

    # Build set of current files with their modification times
    current_files = {}
    for file_path in files:
        stat = file_path.stat()
        file_key = str(file_path.name)
        mtime = stat.st_mtime
        current_files[file_key] = mtime

    # Find files that are new or modified since last check
    new_or_modified = []
    for file_key, mtime in current_files.items():
        if file_key not in cursor or cursor.get(file_key) != mtime:
            new_or_modified.append(file_key)

    if not new_or_modified:
        return SkipReason(f"No new or modified files (tracking {len(files)} files)")

    # Trigger ingestion
    context.log.info(
        f"Detected {len(new_or_modified)} new/modified files: {', '.join(new_or_modified[:5])}"
        + ("..." if len(new_or_modified) > 5 else "")
    )

    # Update cursor with all current files
    context.update_cursor(str(current_files))

    # Return run request
    return RunRequest(
        run_key=f"file_drop_{context.sensor_name}_{context.last_completion_time or 'initial'}",
        run_config={},
        tags={
            "file_count": str(len(new_or_modified)),
            "files": ",".join(new_or_modified[:10]),  # Limit tag size
        },
    )
