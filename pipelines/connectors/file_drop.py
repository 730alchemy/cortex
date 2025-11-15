"""File drop connector - watches a directory for new files."""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional
import puremagic
import structlog

from connectors.base import Connector, FetchedItem

logger = structlog.get_logger()


class FileDropConnector(Connector):
    """Connector that monitors a directory for files to ingest."""

    def __init__(
        self,
        watch_directory: str | Path,
        source_name: str = "file_drop",
        recursive: bool = False,
        file_extensions: Optional[list[str]] = None,
    ):
        """
        Initialize file drop connector.

        Args:
            watch_directory: Directory to watch for files
            source_name: Name of the source (used in source_id)
            recursive: Whether to recursively scan subdirectories
            file_extensions: List of allowed file extensions (e.g., ['.md', '.txt'])
                           If None, all files are allowed
        """
        self.watch_directory = Path(watch_directory)
        self.source_name = source_name
        self.recursive = recursive
        self.file_extensions = file_extensions

        if not self.watch_directory.exists():
            logger.warning(
                "watch_directory_not_found",
                directory=str(self.watch_directory)
            )
            self.watch_directory.mkdir(parents=True, exist_ok=True)
            logger.info("watch_directory_created", directory=str(self.watch_directory))

    def discover(self) -> Iterator[str]:
        """
        Discover files in the watch directory.

        Yields:
            Relative file paths as external IDs
        """
        pattern = "**/*" if self.recursive else "*"

        for file_path in self.watch_directory.glob(pattern):
            # Skip directories
            if not file_path.is_file():
                continue

            # Filter by extension if specified
            if self.file_extensions and file_path.suffix not in self.file_extensions:
                continue

            # Skip hidden files
            if file_path.name.startswith("."):
                continue

            # Use relative path as external ID
            relative_path = file_path.relative_to(self.watch_directory)
            yield str(relative_path)

    def fetch(self, external_id: str) -> FetchedItem:
        """
        Fetch a file from the watch directory.

        Args:
            external_id: Relative path to the file

        Returns:
            FetchedItem with file content and metadata
        """
        file_path = self.watch_directory / external_id

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info("fetching_file", path=str(file_path))

        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()

        # Detect MIME type
        try:
            mime_type = puremagic.from_file(str(file_path), mime=True)
        except Exception as e:
            logger.warning("mime_detection_failed", path=str(file_path), error=str(e))
            mime_type = "application/octet-stream"

        # Get file stats
        stat = file_path.stat()
        size_bytes = stat.st_size
        modified_at = datetime.fromtimestamp(stat.st_mtime)

        # Build source ID
        source_id = f"{self.source_name}::{external_id}"

        return FetchedItem(
            content=content,
            source_id=source_id,
            mime_type=mime_type,
            size_bytes=size_bytes,
            url=f"file://{file_path.absolute()}",
            etag=None,  # File system doesn't have ETags
            license=None,  # Could be inferred from file content in the future
            fetched_at=datetime.utcnow(),
            metadata={
                "file_name": file_path.name,
                "file_extension": file_path.suffix,
                "modified_at": modified_at.isoformat(),
                "absolute_path": str(file_path.absolute()),
            }
        )

    def fingerprint(self, external_id: str) -> str:
        """
        Get file fingerprint based on modification time and size.

        Args:
            external_id: Relative path to the file

        Returns:
            Fingerprint string combining mtime and size
        """
        file_path = self.watch_directory / external_id

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = file_path.stat()
        # Combine mtime and size for fingerprint
        return f"{stat.st_mtime}:{stat.st_size}"

    @staticmethod
    def compute_doc_id(content: bytes) -> str:
        """
        Compute content-addressable document ID (SHA256 hash).

        Args:
            content: File content bytes

        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(content).hexdigest()
