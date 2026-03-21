// Scenario 09: Delete Family
// Benchmarks deleting the two biological parents and one sibling
// that were previously inserted for benchmarking purposes.
// The records are associated with an adopted individual who has
// no biological parents in the dataset, as identified in summary.txt

MATCH (f:Family {id: 20001}) DETACH DELETE f;
MATCH (p:Person) WHERE p.id IN [20001, 20002, 20003] DETACH DELETE p;