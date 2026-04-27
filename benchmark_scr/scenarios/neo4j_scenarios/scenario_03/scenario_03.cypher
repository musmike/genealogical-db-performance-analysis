// Scenario 03: Births per City per Quarter-Century
// Aggregates birth counts grouped by birth_place and 25-year period.
// Should return the columns in the following order and with the following names:
// city, quarter_century_start, birth_count.
// Orders the results by city ascending and quarter_century_start ascending.


MATCH (p:Person)
WHERE p.birthDate IS NOT NULL AND p.birthPlace IS NOT NULL
WITH p.birthPlace AS city,
     (p.birthDate.year / 25) * 25 AS quarter_century_start
RETURN 
    city                    AS city,
    quarter_century_start   AS quarter_century_start,
    COUNT(*)                AS birth_count
ORDER BY city ASC, quarter_century_start ASC;