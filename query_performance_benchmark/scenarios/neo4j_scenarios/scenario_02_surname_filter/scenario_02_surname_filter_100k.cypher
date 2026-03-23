// Scenario 02: Surname and Birth Year Filter
// Filters individuals by a selected surname and a 50-year birth window.
// The surname and window are chosen from summary.txt to return
// a representative (non-trivial) result set.

MATCH (n:person)
WHERE n.birthDate.year >= 1530 and n.birthDate.year <= 1579
AND n.surname = 'Adamczyk'
RETURN n;