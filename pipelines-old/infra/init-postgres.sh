#!/bin/bash
set -e

echo "Running PostgreSQL initialization script..."
echo "Creating databases for Cortex services..."

# Create additional databases needed by services
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
    -- Create dagster database for Dagster metadata
    SELECT 'CREATE DATABASE dagster OWNER ${POSTGRES_USER}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dagster')\gexec

    -- Create marquez database for lineage tracking
    SELECT 'CREATE DATABASE marquez OWNER ${POSTGRES_USER}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'marquez')\gexec

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE dagster TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON DATABASE marquez TO ${POSTGRES_USER};
EOSQL

echo "✓ Databases created successfully!"
echo "  - dagster database (owner: ${POSTGRES_USER})"
echo "  - marquez database (owner: ${POSTGRES_USER})"
