// Scenario 02: Surname and Birth Year Filter
// Filters individuals by a selected surname and a 50-year birth window.
// The surname and window are chosen from summary.txt to return
// a representative (non-trivial) result set.

MATCH (n:person)
WHERE n.birthDate.year >= 1805 and n.birthDate.year <= 1854
AND n.surname = 'Stępień'
RETURN n;