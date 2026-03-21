docker stop neo4j_db
docker run --rm -v db_setup_neo4j_data:/data neo4j:5.26.21-community \
  rm -rf /data/databases/neo4j /data/transactions/neo4j
sync; echo 3 > /proc/sys/vm/drop_caches

docker run --rm \
  -v db_setup_neo4j_data:/data \
  -v $(pwd)/../../data_generator/output:/import:ro \
  neo4j:5.26.21-community \
  neo4j-admin database import full neo4j \
  --id-type=integer \
  --nodes=Person=/import/1k/neo4j/nodes_person.csv \
  --nodes=Family=/import/1k/neo4j/nodes_family.csv \
  --relationships=HUSBAND_OF=/import/1k/neo4j/rels_husband_of.csv \
  --relationships=WIFE_OF=/import/1k/neo4j/rels_wife_of.csv \
  --relationships=HAS_CHILD=/import/1k/neo4j/rels_child_of.csv

docker start neo4j_db