// Scenario 02: Surname and Birth Year Filter
// Filters individuals by a selected surname and a 50-year birth window.
// The surname and window are chosen from expected_results/scenario_02_surname_filter_1k.txt to return
// a representative (non-trivial) result set.
// Should return the columns in the following order and with the following names:
// person_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place.
// Orders the results by birth_date ascending.


// RECOMMENDED PARAMETERS: Surname = 'Pawłowski', Birth Year Range = 1835-1884

MATCH (n:Person)
WHERE n.birthDate.year >= 1835 and n.birthDate.year <= 1884
AND n.surname = 'Pawłowski'
RETURN 
n.id as id,
n.givenName as name,
n.surname as surname,
n.birthDate as birth_date,
n.sex as sex
;