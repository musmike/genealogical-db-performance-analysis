#!/bin/bash

# Terminate active connections to the database before dropping it
docker exec -i postgres_db psql -U user -d postgres -qAt -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'benchmarkdb'
  AND pid <> pg_backend_pid();
"

# Drop the database if it exists
docker exec postgres_db psql -q -U user -d postgres -c "DROP DATABASE IF EXISTS benchmarkdb;"

# Create the benchmark database
docker exec postgres_db psql -q -U user -d postgres -c "CREATE DATABASE benchmarkdb;"