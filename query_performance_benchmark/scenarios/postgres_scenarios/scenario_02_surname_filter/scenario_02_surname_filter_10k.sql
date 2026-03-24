-- Scenario 02: Surname and Birth Year Filter
-- Filters individuals by a selected surname and a 50-year birth window.
-- The surname and window are chosen from summary.txt to return
-- a representative (non-trivial) result set.

SELECT
    p.id,
    p.given_name,
    p.surname,
    p.birth_date,
    p.birth_place,
    p.sex,
    p.death_date
FROM people p
WHERE p.surname = 'Stępień'
  AND p.birth_date IS NOT NULL
  AND EXTRACT(YEAR FROM p.birth_date) BETWEEN 1796 AND 1845
ORDER BY p.birth_date;