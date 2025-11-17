import os
from pathlib import Path
import dagster as dg

from .assets import assetsRaw


@dg.sensor(
    target=None,
    asset_selection=[assetsRaw],
    default_status=dg.DefaultSensorStatus.RUNNING
)
def sensors(context: dg.SensorEvaluationContext) -> dg.SensorResult:
    """
    Sensor that monitors a directory for new files and triggers asset materialization.

    Directory path is configured via INPUT_DIR environment variable.
    Tracks processed files using sensor cursor to avoid reprocessing.
    """
    # Get directory path from environment variable
    input_dir = os.environ.get('INPUT_DIR')
    context.log.info(f'context cursor: {context.cursor}')

    if not input_dir:
        context.log.warning('INPUT_DIR environment variable not set')
        return dg.SkipReason('INPUT_DIR environment variable not configured')

    input_path = Path(input_dir)

    # Check if directory exists
    if not input_path.exists():
        context.log.warning(f'Directory does not exist: {input_path}')
        return dg.SkipReason(f'Directory does not exist: {input_path}')

    if not input_path.is_dir():
        context.log.error(f'Path is not a directory: {input_path}')
        return dg.SkipReason(f'Path is not a directory: {input_path}')

    # Get all files in directory (not subdirectories)
    try:
        current_files = {str(f.absolute()) for f in input_path.iterdir() if f.is_file()}
    except Exception as e:
        context.log.error(f'Error reading directory {input_path}: {e}')
        return dg.SkipReason(f'Error reading directory: {e}')

    # Get previously seen files from cursor
    cursor = context.cursor or '{}'
    import json
    try:
        seen_files = set(json.loads(cursor))
    except json.JSONDecodeError:
        seen_files = set()

    # Identify new files
    new_files = current_files - seen_files

    if not new_files:
        context.log.info(f'No new files detected in {input_path}')
        return dg.SkipReason('No new files detected')

    # Log new files found
    context.log.info(f'Detected {len(new_files)} new file(s) in {input_path}')
    for file_path in sorted(new_files):
        context.log.info(f'  - {Path(file_path).name}')

    # Update cursor with all currently seen files
    context.update_cursor(json.dumps(list(current_files)))

    # Trigger asset materialization with new file paths as metadata
    return dg.RunRequest(
        run_config={
            'ops': {
                'assetsRaw': {
                    'config': {
                        'new_files': sorted(list(new_files))
                    }
                }
            }
        },
        tags={
            'new_file_count': str(len(new_files)),
            'input_directory': str(input_path)
        }
    )
