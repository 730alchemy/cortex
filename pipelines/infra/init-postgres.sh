#!/bin/bash
set -e

# Create additional databases needed by services
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create dagster database for Dagster metadata
    SELECT 'CREATE DATABASE dagster'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dagster')\gexec

    -- Create marquez database for lineage tracking
    SELECT 'CREATE DATABASE marquez'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'marquez')\gexec

    -- Grant privileges to main user (cortex)
    GRANT ALL PRIVILEGES ON DATABASE dagster TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE marquez TO $POSTGRES_USER;
EOSQL

echo "Additional databases created successfully!"
