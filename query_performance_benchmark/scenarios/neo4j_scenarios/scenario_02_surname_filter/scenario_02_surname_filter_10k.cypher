// Scenario 02: Surname and Birth Year Filter
// Filters individuals by a selected surname and a 50-year birth window.
// The surname and window are chosen from summary.txt to return
// a representative (non-trivial) result set.

MATCH (n:Person)
WHERE n.birthDate.year >= 1796 and n.birthDate.year <= 1845
AND n.surname = 'Stępień'
RETURN 
n.id as id,
n.givenName as name,
n.surname as surname,
n.birthDate as birth_date,
n.sex as sex
;