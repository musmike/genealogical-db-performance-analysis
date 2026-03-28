#!/bin/bash

# Stop and drop existing database if exists
docker exec -it neo4j_db cypher-shell -u neo4j -p password --database system \
  "STOP DATABASE benchmarkdb" 2>/dev/null || true
docker exec -it neo4j_db cypher-shell -u neo4j -p password --database system \
  "DROP DATABASE benchmarkdb IF EXISTS DESTROY DATA" 2>/dev/null || true
docker exec -it neo4j_db rm -rf /data/databases/benchmarkdb
docker exec -it neo4j_db rm -rf /data/transactions/benchmarkdb

# Import data using neo4j-admin tool and capture output for timing
OUTPUT=$(docker exec -i neo4j_db \
  neo4j-admin database import full benchmarkdb \
  --id-type=integer \
  --nodes=Person=/import/1k/neo4j/nodes_person.csv \
  --nodes=Family=/import/1k/neo4j/nodes_family.csv \
  --relationships=HUSBAND_OF=/import/1k/neo4j/rels_husband_of.csv \
  --relationships=WIFE_OF=/import/1k/neo4j/rels_wife_of.csv \
  --relationships=HAS_CHILD=/import/1k/neo4j/rels_child_of.csv 2>&1)

echo "$OUTPUT"

if echo "$OUTPUT" | grep -q "IMPORT DONE in"; then
  if [[ $OUTPUT =~ IMPORT\ DONE\ in\ (([0-9]+)m\ )?(([0-9]+)s\ )?(([0-9]+)ms)? ]]; then
    MINUTES=${BASH_REMATCH[2]:-0}
    SECONDS=${BASH_REMATCH[4]:-0}
    MILLIS=${BASH_REMATCH[6]:-0}
    TOTAL_MS=$(( MINUTES * 60000 + SECONDS * 1000 + MILLIS ))
    # Output the total time in milliseconds for use in the benchmark
    echo "NEO4J_IMPORT_MS=$TOTAL_MS"
  fi
else
  echo "NEO4J_IMPORT FAILED"
  exit 1
fi

# Create the benchmarkdb database and start it
docker exec -it neo4j_db cypher-shell -u neo4j -p password --database system \
  "CREATE DATABASE benchmarkdb IF NOT EXISTS"
docker exec -it neo4j_db cypher-shell -u neo4j -p password --database system \
  "START DATABASE benchmarkdb"