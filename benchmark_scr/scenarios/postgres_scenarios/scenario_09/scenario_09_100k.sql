-- Scenario 09: Delete Family
-- Benchmarks deleting the two biological parents and one sibling
-- that were previously inserted for benchmarking purposes.
-- The records are associated with an adopted individual who has
-- no biological parents in the dataset, as identified in expected_results/scenario_08_09_insert_delete.txt


DELETE FROM families
WHERE id = 200001;

DELETE FROM people 
WHERE id IN (200001, 200002, 200003);