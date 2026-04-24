// Scenario 02: Surname and Birth Year Filter
// Filters individuals by a selected surname and a 50-year birth window.
// The surname and window are chosen from expected_results/scenario_02_surname_filter_100k.txt to return
// a representative (non-trivial) result set.
// Should return the columns in the following order and with the following names:
// person_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place.
// Orders the results by birth_date ascending.


// RECOMMENDED PARAMETERS: Surname = 'Górski', Birth Year Range = 1461-1510

MATCH (p:Person)
WHERE p.surname = 'Górski' 
    AND p.birthDate >= date('1461-01-01') AND p.birthDate <= date('1510-12-31')
RETURN
    p.id            AS person_id, 
    p.givenName     AS given_name, 
    p.surname       AS surname, 
    p.sex           AS sex, 
    p.birthDate     AS birth_date, 
    p.birthPlace    AS birth_place, 
    p.deathDate     AS death_date, 
    p.deathPlace    AS death_place
ORDER BY p.birthDate ASC;