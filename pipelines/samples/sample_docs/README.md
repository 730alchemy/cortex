# Sample Documents

This directory contains sample documents for testing the data pipeline ingestion.

## Files

- **project_overview.md**: Sample project documentation
- **technical_spec.txt**: Sample technical specification
- **meeting_notes.md**: Sample meeting notes

## Usage

To test ingestion, copy files from this directory to `../watch/file_drop/`:

```bash
cp samples/sample_docs/* samples/watch/file_drop/
```

The Dagster sensor will detect the files within 30 seconds and trigger ingestion.

## File Types Supported

The pipeline currently supports:
- Markdown (.md)
- Text (.txt)
- PDF (.pdf)
- HTML (.html)
- JSON (.json)
- YAML (.yaml, .yml)

Files are deduplicated by content hash (SHA256), so uploading the same file twice will only result in one entry in the catalog.
