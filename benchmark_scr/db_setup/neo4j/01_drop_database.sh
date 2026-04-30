#!/bin/bash

# Drop existing database if exists and remove data files to ensure a clean import
docker exec neo4j_db cypher-shell -u neo4j -p password --database system \
  "DROP DATABASE benchmarkdb IF EXISTS DESTROY DATA" 2>/dev/null || true
docker exec neo4j_db rm -rf /data/databases/benchmarkdb /data/transactions/benchmarkdb