-- Scenario 01: Lowest Common Ancestor (LCA)
-- Finds the closest common biological ancestor of two selected individuals.
-- The specific pair of person IDs is taken from expected_results/scenario_01_lca_100k.txt —
-- chosen such that the total path length through the LCA matches the
-- configured target (16 hops for 100k).
-- Traversal follows biological relationships only (adopted/foster excluded).
-- Should return the columns in the following order and with the following names:
-- lca_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place, path_length_from_a, path_length_from_b, total_dist.
-- Orders the results by lca_id ascending.


-- RECOMMENDED PARAMETERS: Person A = 92308, Person B = 96653

WITH RECURSIVE
anc_a(person_id, depth, visited) AS (
    SELECT 92308, 0, ARRAY[92308]
    UNION ALL
    SELECT parent_id, a.depth + 1, a.visited || parent_id
    FROM anc_a a
    JOIN family_children fc ON fc.child_id = a.person_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN families f ON f.id = fc.family_id
    CROSS JOIN LATERAL (
        VALUES (f.husband_id), (f.wife_id)
    ) AS parents(parent_id)
    WHERE a.depth < 16 AND NOT (parent_id = ANY(a.visited))
),
anc_b(person_id, depth, visited) AS (
    SELECT 96653, 0, ARRAY[96653]
    UNION ALL
    SELECT parent_id, b.depth + 1, b.visited || parent_id
    FROM anc_b b
    JOIN family_children fc ON fc.child_id = b.person_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN families f ON f.id = fc.family_id
    CROSS JOIN LATERAL (
        VALUES (f.husband_id), (f.wife_id)
    ) AS parents(parent_id)
    WHERE b.depth < 16 AND NOT (parent_id = ANY(b.visited))
),
min_a AS (
    SELECT person_id, MIN(depth) AS depth FROM anc_a GROUP BY person_id
),
min_b AS (
    SELECT person_id, MIN(depth) AS depth FROM anc_b GROUP BY person_id
),
common AS (
    SELECT a.person_id, a.depth AS dist_a, b.depth AS dist_b, a.depth + b.depth AS total_dist
    FROM min_a a
    JOIN min_b b ON b.person_id = a.person_id
)
SELECT c.person_id AS lca_id, p.given_name, p.surname, p.sex,
       p.birth_date, p.birth_place, p.death_date, p.death_place,
       c.dist_a AS path_length_from_a, c.dist_b AS path_length_from_b, c.total_dist
FROM common c
JOIN people p ON p.id = c.person_id
WHERE c.total_dist = (SELECT MIN(total_dist) FROM common)
ORDER BY c.person_id;