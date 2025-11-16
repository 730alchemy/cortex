"""Base connector interface for all data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Optional


@dataclass
class FetchedItem:
    """Represents a fetched document with metadata."""

    content: bytes
    source_id: str  # External identifier (e.g., "file_drop::readme.md")
    mime_type: str
    size_bytes: int
    url: Optional[str] = None
    etag: Optional[str] = None
    license: Optional[str] = None
    fetched_at: Optional[datetime] = None
    metadata: Optional[dict] = None  # Additional source-specific metadata


class Connector(ABC):
    """Abstract base class for all connectors."""

    @abstractmethod
    def discover(self) -> Iterator[str]:
        """
        Discover available items to fetch.

        Yields:
            External IDs of items to fetch
        """
        pass

    @abstractmethod
    def fetch(self, external_id: str) -> FetchedItem:
        """
        Fetch a single item by its external ID.

        Args:
            external_id: The external identifier of the item

        Returns:
            FetchedItem with content and metadata
        """
        pass

    @abstractmethod
    def fingerprint(self, external_id: str) -> str:
        """
        Get a fingerprint (etag, last_modified, etc.) for change detection.

        Args:
            external_id: The external identifier

        Returns:
            Fingerprint string for change detection
        """
        pass

    def fetch_all(self) -> Iterator[FetchedItem]:
        """
        Discover and fetch all items.

        Yields:
            FetchedItem for each discovered item
        """
        for external_id in self.discover():
            try:
                yield self.fetch(external_id)
            except Exception as e:
                # Log error but continue with other items
                print(f"Error fetching {external_id}: {e}")
                continue
