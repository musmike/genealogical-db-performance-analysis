-- Scenario 09: Delete Family
-- Benchmarks deleting the two biological parents and one sibling
-- that were previously inserted for benchmarking purposes.
-- The records are associated with an adopted individual who has
-- no biological parents in the dataset, as identified in summary.txt


DELETE FROM family_children WHERE family_id = 20001;
DELETE FROM families        WHERE id        = 20001;
DELETE FROM people          WHERE id IN (20001, 20002, 20003);