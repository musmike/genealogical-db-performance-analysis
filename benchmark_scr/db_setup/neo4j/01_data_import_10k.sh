#!/bin/bash

# Drop existing database if exists
docker exec neo4j_db cypher-shell -u neo4j -p password --database system \
  "DROP DATABASE benchmarkdb IF EXISTS DESTROY DATA" 2>/dev/null || true
docker exec neo4j_db rm -rf /data/databases/benchmarkdb /data/transactions/benchmarkdb

# Import data using neo4j-admin tool and capture output for timing
OUTPUT=$(docker exec neo4j_db \
  neo4j-admin database import full benchmarkdb \
  --id-type=integer \
  --nodes=Person=/import/10k/neo4j/nodes_person.csv \
  --nodes=Family=/import/10k/neo4j/nodes_family.csv \
  --relationships=HUSBAND_OF=/import/10k/neo4j/rels_husband_of.csv \
  --relationships=WIFE_OF=/import/10k/neo4j/rels_wife_of.csv \
  --relationships=HAS_BIOLOGICAL_CHILD=/import/10k/neo4j/rels_has_biological_child.csv \
  --relationships=HAS_ADOPTED_CHILD=/import/10k/neo4j/rels_has_adopted_child.csv \
  --relationships=HAS_FOSTER_CHILD=/import/10k/neo4j/rels_has_foster_child.csv 2>&1)

# Display the exact "IMPORT DONE ..." line from output
IMPORT_LINE=$(echo "$OUTPUT" | grep "IMPORT DONE")
echo "$IMPORT_LINE"

# Parse the time and convert to milliseconds
if [[ $IMPORT_LINE =~ IMPORT\ DONE\ in\ (([0-9]+)m\ )?(([0-9]+)s\ )?([0-9]+)ms\. ]]; then
  MINUTES=${BASH_REMATCH[2]:-0}
  SECONDS=${BASH_REMATCH[4]:-0}
  MILLIS=${BASH_REMATCH[5]}
  echo "NEO4J_IMPORT_MS=$(( MINUTES*60000 + SECONDS*1000 + MILLIS ))"
else
  echo "NEO4J_IMPORT FAILED"
  echo "$OUTPUT"
  exit 1
fi