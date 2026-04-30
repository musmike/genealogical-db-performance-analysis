#!/bin/bash

# Restart the database to ensure the imported data is fully loaded and available for queries
docker restart neo4j_db

# Wait until the database is available before proceeding
until docker exec neo4j_db cypher-shell -u neo4j -p password \
  "RETURN 1;" 2>/dev/null | grep -q "1"; do sleep 2; done

# Create and start the benchmark database
docker exec neo4j_db cypher-shell -u neo4j -p password --database system \
  "CREATE DATABASE benchmarkdb IF NOT EXISTS"
docker exec neo4j_db cypher-shell -u neo4j -p password --database system \
  "START DATABASE benchmarkdb WAIT"