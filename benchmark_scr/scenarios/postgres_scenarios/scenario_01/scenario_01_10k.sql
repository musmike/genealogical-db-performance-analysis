-- Scenario 01: Lowest Common Ancestor (LCA)
-- Finds the closest common biological ancestor of two selected individuals.
-- The specific pair of person IDs is taken from expected_results/scenario_01_lca_10k.txt —
-- chosen such that the total path length through the LCA matches the
-- configured target (12 hops for 10k dataset).
-- Traversal follows biological relationships only (adopted/foster excluded).
-- Should return the columns in the following order and with the following names:
-- lca_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place, path_length_from_a, path_length_from_b, total_dist.
-- Orders the results by lca_id ascending.


-- RECOMMENDED PARAMETERS: Person A = 8844, Person B = 6972

WITH RECURSIVE 
anc_a AS (
    SELECT 8844 AS person_id, 0 AS depth
    UNION
    SELECT parent_id, a.depth + 1
    FROM anc_a a
    JOIN family_children fc ON fc.child_id = a.person_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN families f ON f.id = fc.family_id
    CROSS JOIN LATERAL (
        VALUES (f.husband_id), (f.wife_id)
    ) AS parents(parent_id)
    WHERE a.depth < 12 
    AND parents.parent_id IS NOT NULL
),
anc_b AS (
    SELECT 6972 AS person_id, 0 AS depth
    UNION
    SELECT parent_id, b.depth + 1
    FROM anc_b b
    JOIN family_children fc ON fc.child_id = b.person_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN families f ON f.id = fc.family_id
    CROSS JOIN LATERAL (
        VALUES (f.husband_id), (f.wife_id)
    ) AS parents(parent_id)
    WHERE b.depth < 12 
    AND parents.parent_id IS NOT NULL
),
min_a AS (
    SELECT DISTINCT ON (person_id) person_id, depth FROM anc_a ORDER BY person_id, depth
),
min_b AS (
    SELECT DISTINCT ON (person_id) person_id, depth FROM anc_b ORDER BY person_id, depth
),
common AS (
    SELECT a.person_id, a.depth AS dist_a, b.depth AS dist_b, a.depth + b.depth AS total_dist
    FROM min_a a
    JOIN min_b b ON b.person_id = a.person_id
)
SELECT 
    c.person_id     AS lca_id, 
    p.given_name    AS given_name, 
    p.surname       AS surname, 
    p.sex           AS sex, 
    p.birth_date    AS birth_date, 
    p.birth_place   AS birth_place, 
    p.death_date    AS death_date, 
    p.death_place   AS death_place, 
    c.dist_a        AS path_length_from_a, 
    c.dist_b        AS path_length_from_b, 
    c.total_dist    AS total_dist
FROM common c
JOIN people p ON p.id = c.person_id
WHERE c.total_dist = (SELECT MIN(total_dist) FROM common)
ORDER BY lca_id ASC;