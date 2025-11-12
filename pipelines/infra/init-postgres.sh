#!/bin/bash
set -e

# Create additional databases and users needed by services
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create marquez user for Marquez service
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'marquez') THEN
            CREATE USER marquez WITH PASSWORD '$POSTGRES_PASSWORD';
        END IF;
    END
    \$\$;

    -- Create dagster database for Dagster metadata
    SELECT 'CREATE DATABASE dagster'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dagster')\gexec

    -- Create marquez database for lineage tracking
    SELECT 'CREATE DATABASE marquez'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'marquez')\gexec

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE dagster TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE marquez TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE marquez TO marquez;
EOSQL

echo "Additional databases and users created successfully!"
