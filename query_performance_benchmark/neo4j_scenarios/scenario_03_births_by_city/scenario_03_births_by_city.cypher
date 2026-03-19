// Scenario 03: Births per City per Quarter-Century
// Aggregates birth counts grouped by birth_place and 25-year period.

MATCH (p:Person)
WHERE p.birthDate IS NOT NULL AND p.birthPlace IS NOT NULL

WITH p.birthPlace                        AS city,
     (p.birthDate.year / 25) * 25        AS qc,
     count(*)                            AS births

WITH city,
     collect({ qc: qc, births: births }) AS buckets,
     sum(births)                          AS total_births

ORDER BY total_births DESC
LIMIT 10

UNWIND buckets AS b

RETURN city,
       b.qc      AS quarter_century_start,
       b.births  AS births
ORDER BY city, quarter_century_start;