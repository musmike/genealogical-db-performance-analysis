// Scenario 02: Surname and Birth Year Filter
// Filters individuals by a selected surname and a 50-year birth window.
// The surname and window are chosen from expected_results/scenario_02_surname_filter_10k.txt to return
// a representative (non-trivial) result set.
// Should return the columns in the following order and with the following names:
// person_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place.
// Orders the results by birth_date ascending.


// RECOMMENDED PARAMETERS: Surname = 'Zając', Birth Year Range = 1744-1793

MATCH (n:Person)
WHERE n.birthDate.year >= 1744 and n.birthDate.year <= 1793
AND n.surname = 'Zając'
RETURN 
n.id as person_id,
n.givenName as given_name,
n.surname as surname,
n.sex as sex,
n.birthDate as birth_date,
n.deathDate as death_date,
n.deathPlace as death_place
ORDER BY n.birthDate ASC
;