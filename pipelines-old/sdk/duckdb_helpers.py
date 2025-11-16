"""DuckDB helper functions and common queries."""

from typing import List, Dict, Any
from catalog.duckdb_manager import get_duckdb_manager


def list_tables() -> List[str]:
    """List all available Iceberg tables."""
    con = get_duckdb_manager().get_connection()
    result = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'iceberg_catalog'
        ORDER BY table_name
    """
    ).fetchall()
    return [row[0] for row in result]


def table_row_count(table_name: str) -> int:
    """Get row count for a table."""
    con = get_duckdb_manager().get_connection()
    result = con.execute(
        f"""
        SELECT COUNT(*)
        FROM iceberg_scan('s3://warehouse/catalog/{table_name}')
    """
    ).fetchone()
    return result[0] if result else 0


def recent_docs(limit: int = 10) -> List[Dict[str, Any]]:
    """Get most recently ingested documents."""
    con = get_duckdb_manager().get_connection()
    result = con.execute(
        f"""
        SELECT doc_id, source_id, mime, size_bytes, ingest_first_at
        FROM iceberg_scan('s3://warehouse/catalog/docs')
        ORDER BY ingest_first_at DESC
        LIMIT {limit}
    """
    )

    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def docs_by_source() -> Dict[str, int]:
    """Get document counts by source."""
    con = get_duckdb_manager().get_connection()
    result = con.execute(
        """
        SELECT source_id, COUNT(*) as count
        FROM iceberg_scan('s3://warehouse/catalog/docs')
        GROUP BY source_id
        ORDER BY count DESC
    """
    ).fetchall()
    return {row[0]: row[1] for row in result}


def docs_by_mime_type() -> Dict[str, int]:
    """Get document counts by MIME type."""
    con = get_duckdb_manager().get_connection()
    result = con.execute(
        """
        SELECT mime, COUNT(*) as count
        FROM iceberg_scan('s3://warehouse/catalog/docs')
        GROUP BY mime
        ORDER BY count DESC
    """
    ).fetchall()
    return {row[0]: row[1] for row in result}


def time_travel_query(table_name: str, timestamp: str) -> List[Dict[str, Any]]:
    """
    Query table at a specific point in time (Iceberg time travel).

    Args:
        table_name: Name of the Iceberg table
        timestamp: ISO timestamp string

    Returns:
        List of row dicts at that timestamp
    """
    con = get_duckdb_manager().get_connection()
    result = con.execute(
        f"""
        SELECT *
        FROM iceberg_scan('s3://warehouse/catalog/{table_name}')
        FOR SYSTEM_TIME AS OF '{timestamp}'
    """
    )

    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def search_docs(search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search documents by source_id or doc_id.

    Args:
        search_term: Term to search for
        limit: Maximum results to return

    Returns:
        List of matching document dicts
    """
    con = get_duckdb_manager().get_connection()
    result = con.execute(
        f"""
        SELECT doc_id, source_id, mime, size_bytes, ingest_first_at
        FROM iceberg_scan('s3://warehouse/catalog/docs')
        WHERE source_id LIKE ? OR doc_id LIKE ?
        ORDER BY ingest_first_at DESC
        LIMIT {limit}
    """,
        [f"%{search_term}%", f"%{search_term}%"],
    )

    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


# Convenience SQL templates
SQL_TEMPLATES = {
    "all_docs": """
        SELECT * FROM iceberg_scan('s3://warehouse/catalog/docs')
        ORDER BY ingest_first_at DESC
    """,
    "docs_summary": """
        SELECT
            COUNT(*) as total_docs,
            COUNT(DISTINCT source_id) as unique_sources,
            SUM(size_bytes) / 1024 / 1024 as total_mb,
            MIN(ingest_first_at) as first_ingest,
            MAX(ingest_last_at) as last_ingest
        FROM iceberg_scan('s3://warehouse/catalog/docs')
    """,
    "doc_versions_for_id": """
        SELECT * FROM iceberg_scan('s3://warehouse/catalog/doc_versions')
        WHERE doc_id = ?
        ORDER BY ingest_at DESC
    """,
    "recent_lineage_events": """
        SELECT * FROM iceberg_scan('s3://warehouse/catalog/events_lineage')
        ORDER BY event_time DESC
        LIMIT 50
    """,
}


def execute_template(template_name: str, params: List = None) -> List[Dict[str, Any]]:
    """
    Execute a predefined SQL template.

    Args:
        template_name: Name of template in SQL_TEMPLATES
        params: Parameters for placeholders

    Returns:
        List of result dicts
    """
    if template_name not in SQL_TEMPLATES:
        raise ValueError(
            f"Unknown template: {template_name}. Available: {list(SQL_TEMPLATES.keys())}"
        )

    con = get_duckdb_manager().get_connection()
    sql = SQL_TEMPLATES[template_name]
    result = con.execute(sql, params or [])

    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]
