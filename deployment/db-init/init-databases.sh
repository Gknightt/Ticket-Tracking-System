#!/bin/bash
set -e

# Create databases for each service
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    -- Create databases if they don't exist
    SELECT 'CREATE DATABASE auth_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'auth_db')\gexec

    SELECT 'CREATE DATABASE workflow_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'workflow_db')\gexec

    SELECT 'CREATE DATABASE workflowmanagement'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'workflowmanagement')\gexec

    SELECT 'CREATE DATABASE ticket_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ticket_db')\gexec

    SELECT 'CREATE DATABASE messaging_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'messaging_db')\gexec

    SELECT 'CREATE DATABASE notification_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'notification_db')\gexec

    SELECT 'CREATE DATABASE notificationservice'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'notificationservice')\gexec

    -- Grant all privileges
    GRANT ALL PRIVILEGES ON DATABASE auth_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE workflow_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE workflowmanagement TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE ticket_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE messaging_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE notification_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE notificationservice TO $POSTGRES_USER;
EOSQL

echo "Databases created successfully!"
