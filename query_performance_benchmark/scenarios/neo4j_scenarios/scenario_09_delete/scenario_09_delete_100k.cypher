// Scenario 09: Delete Family
// Benchmarks deleting the two biological parents and one sibling
// that were previously inserted for benchmarking purposes.
// The records are associated with an adopted individual who has
// no biological parents in the dataset, as identified in expected_results/scenario_09_delete_1k.txt.

MATCH (f:Family {id: 200001}) DETACH DELETE f;
MATCH (p:Person) WHERE p.id IN [200001, 200002, 200003] DETACH DELETE p;