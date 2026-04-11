-- Scenario 02: Surname and Birth Year Filter
-- Filters individuals by a selected surname and a 50-year birth window.
-- The surname and window are chosen from expected_results/scenario_02_surname_filter_1k.txt to return
-- a representative (non-trivial) result set.
-- Should return the columns in the following order and with the following names:
-- person_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place.
-- Orders the results by birth_date ascending.


-- RECOMMENDED PARAMETERS: Surname = 'Michalski', Birth Year Range = 1814-1863

SELECT
    p.id AS person_id,
    p.given_name,
    p.surname,
    p.sex,
    p.birth_date,
    p.death_date,
    p.birth_place
FROM people p
WHERE p.surname = 'Michalski'
  AND EXTRACT(YEAR FROM p.birth_date) BETWEEN 1814 AND 1863
ORDER BY p.birth_date ASC;