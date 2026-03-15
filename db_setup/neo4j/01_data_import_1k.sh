
# docker exec neo4j_db neo4j stop
# docker exec neo4j_db rm -rf /data/databases/neo4j /data/transactions/neo4j

docker exec neo4j_db neo4j-admin database import full neo4j \
  --nodes=Person=/import/1k/neo4j/nodes_person.csv \
  --nodes=Family=/import/1k/neo4j/nodes_family.csv \
  --relationships=HUSBAND_OF=/import/1k/neo4j/rels_husband_of.csv \
  --relationships=WIFE_OF=/import/1k/neo4j/rels_wife_of.csv \
  --relationships=HAS_CHILD=/import/1k/neo4j/rels_child_of.csv

# docker exec neo4j_db neo4j start