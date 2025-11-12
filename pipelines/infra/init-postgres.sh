#!/bin/bash
set -e

echo "Running PostgreSQL initialization script..."
echo "Creating databases and users for Cortex services..."

# Create additional databases and users needed by services
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
    -- Create marquez user (Marquez expects this specific username)
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'marquez') THEN
            CREATE USER marquez WITH PASSWORD '${POSTGRES_PASSWORD}';
            RAISE NOTICE 'Created user: marquez';
        ELSE
            RAISE NOTICE 'User marquez already exists';
        END IF;
    END
    \$\$;

    -- Create dagster database for Dagster metadata
    SELECT 'CREATE DATABASE dagster OWNER ${POSTGRES_USER}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dagster')\gexec

    -- Create marquez database for lineage tracking
    SELECT 'CREATE DATABASE marquez OWNER marquez'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'marquez')\gexec

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE dagster TO ${POSTGRES_USER};
    GRANT ALL PRIVILEGES ON DATABASE marquez TO marquez;
    GRANT ALL PRIVILEGES ON DATABASE marquez TO ${POSTGRES_USER};
EOSQL

echo "✓ Databases and users created successfully!"
echo "  - dagster database (owner: ${POSTGRES_USER})"
echo "  - marquez database (owner: marquez)"
echo "  - marquez user (password: set)"
