#!/bin/bash
set -e

# Create additional databases and users needed by services
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create marquez user (Marquez expects this specific username)
    CREATE USER marquez WITH PASSWORD '$POSTGRES_PASSWORD';

    -- Create dagster database for Dagster metadata
    CREATE DATABASE dagster OWNER $POSTGRES_USER;

    -- Create marquez database for lineage tracking
    CREATE DATABASE marquez OWNER marquez;

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE dagster TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE marquez TO marquez;
    GRANT ALL PRIVILEGES ON DATABASE marquez TO $POSTGRES_USER;
EOSQL

echo "Databases and users created successfully!"
