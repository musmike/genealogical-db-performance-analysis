-- Scenario 02: Surname and Birth Year Filter
-- Filters individuals by a selected surname and a 50-year birth window.
-- The surname and window are chosen from expected_results/scenario_02_surname_filter_10k.txt to return
-- a representative (non-trivial) result set.
-- Should return the columns in the following order and with the following names:
-- person_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place.
-- Orders the results by birth_date ascending.


-- RECOMMENDED PARAMETERS: Surname = 'Adamczyk', Birth Year Range = 1701-1750

SELECT
    p.id,
    p.given_name,
    p.surname,
    p.birth_date,
    p.birth_place,
    p.sex,
    p.death_date
FROM people p
WHERE p.surname = 'Adamczyk'
  AND p.birth_date IS NOT NULL
  AND EXTRACT(YEAR FROM p.birth_date) BETWEEN 1701 AND 1750
ORDER BY p.birth_date;