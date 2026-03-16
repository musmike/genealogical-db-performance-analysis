-- Scenario 01: Lowest Common Ancestor (LCA)
-- Finds the closest common biological ancestor of two selected individuals.
-- The specific pair of person IDs is taken from summary.txt (LCA section) —
-- chosen such that the total path length through the LCA matches the
-- configured target (12 hops for 10k dataset).
-- Traversal follows biological relationships only (adopted/foster excluded).

WITH RECURSIVE
anc_a(person_id, depth, visited) AS (
    SELECT 8013, 0, ARRAY[8013]
    UNION ALL
    SELECT parent.id, a.depth + 1, a.visited || parent.id
    FROM anc_a a
    JOIN family_children fc ON fc.child_id = a.person_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN families f ON f.id = fc.family_id
    JOIN people parent ON parent.id IN (f.husband_id, f.wife_id)
    WHERE a.depth < 12 AND NOT (parent.id = ANY(a.visited))
),
anc_b(person_id, depth, visited) AS (
    SELECT 7085, 0, ARRAY[7085]
    UNION ALL
    SELECT parent.id, a.depth + 1, a.visited || parent.id
    FROM anc_b a
    JOIN family_children fc ON fc.child_id = a.person_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN families f ON f.id = fc.family_id
    JOIN people parent ON parent.id IN (f.husband_id, f.wife_id)
    WHERE a.depth < 12 AND NOT (parent.id = ANY(a.visited))
),
min_a AS (SELECT person_id, MIN(depth) AS depth FROM anc_a GROUP BY person_id),
min_b AS (SELECT person_id, MIN(depth) AS depth FROM anc_b GROUP BY person_id),
common AS (
    SELECT a.person_id, a.depth AS dist_a, b.depth AS dist_b, a.depth + b.depth AS total_dist
    FROM min_a a
    JOIN min_b b ON b.person_id = a.person_id
)
SELECT c.person_id AS lca_id, p.given_name, p.surname,
    p.birth_date, p.birth_place, p.death_date, p.death_place,
    c.dist_a AS path_length_from_a, c.dist_b AS path_length_from_b, c.total_dist
FROM common c
JOIN people p ON p.id = c.person_id
WHERE c.total_dist = (SELECT MIN(total_dist) FROM common)
ORDER BY c.person_id;