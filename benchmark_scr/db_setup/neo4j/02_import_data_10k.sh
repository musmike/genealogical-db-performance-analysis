#!/bin/bash

# Import data using neo4j-admin tool
docker exec neo4j_db \
  neo4j-admin database import full benchmarkdb \
  --id-type=integer \
  --nodes=Person=/import/10k/neo4j/nodes_person.csv \
  --nodes=Family=/import/10k/neo4j/nodes_family.csv \
  --relationships=HUSBAND_OF=/import/10k/neo4j/rels_husband_of.csv \
  --relationships=WIFE_OF=/import/10k/neo4j/rels_wife_of.csv \
  --relationships=HAS_BIOLOGICAL_CHILD=/import/10k/neo4j/rels_has_biological_child.csv \
  --relationships=HAS_ADOPTED_CHILD=/import/10k/neo4j/rels_has_adopted_child.csv \
  --relationships=HAS_FOSTER_CHILD=/import/10k/neo4j/rels_has_foster_child.csv
