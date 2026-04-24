-- Scenario 02: Surname and Birth Year Filter
-- Filters individuals by a selected surname and a 50-year birth window.
-- The surname and window are chosen from expected_results/scenario_02_surname_filter_1k.txt to return
-- a representative (non-trivial) result set.
-- Should return the columns in the following order and with the following names:
-- person_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place.
-- Orders the results by birth_date ascending.


-- RECOMMENDED PARAMETERS: Surname = 'Piotrowski', Birth Year Range = 1738-1787

SELECT
    p.id            AS person_id, 
    p.given_name    AS given_name, 
    p.surname       AS surname, 
    p.sex           AS sex, 
    p.birth_date    AS birth_date, 
    p.birth_place   AS birth_place, 
    p.death_date    AS death_date, 
    p.death_place   AS death_place
FROM people p
WHERE p.surname = 'Piotrowski'
    AND p.birth_date >= '1738-01-01' AND p.birth_date <= '1787-12-31'
ORDER BY p.birth_date ASC;