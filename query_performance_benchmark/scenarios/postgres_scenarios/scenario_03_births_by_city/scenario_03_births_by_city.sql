-- Scenario 03: Births per City per Quarter-Century
-- Aggregates birth counts grouped by birth_place and 25-year period.

SELECT
    p.birth_place AS city,

    ((EXTRACT(YEAR FROM p.birth_date)::int / 25) * 25) AS quarter_century,

    COUNT(*) AS birth_count
FROM people p
WHERE p.birth_date IS NOT NULL
  AND p.birth_place IS NOT NULL
GROUP BY
    p.birth_place,
    (EXTRACT(YEAR FROM p.birth_date)::int / 25)
ORDER BY
    city,
    quarter_century;