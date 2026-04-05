-- Scenario 04: Ancestor Retrieval (100k dataset)
-- Retrieves all distinct biological ancestors of a selected individual
-- up to a configured depth (15 generations in this case).
-- Uses the individual identified in summary.txt as having the most ancestors.
-- Should return the columns in the following order and with the following names:
-- ancestor_id, generation (the shortest path length from the starting individual), given_name, surname,
-- sex, birth_date, birth_place, death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
-- Orders the results first by generation ascending, then by ancestor_id ascending within each generation.

WITH RECURSIVE ancestors AS (
    SELECT 99993 AS person_id, 0 AS depth
    UNION ALL
    SELECT parent_id, a.depth + 1
    FROM ancestors a
    JOIN family_children fc ON fc.child_id = a.person_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN families f ON f.id = fc.family_id
    CROSS JOIN LATERAL (VALUES (f.husband_id),(f.wife_id)) AS v(parent_id)
    WHERE parent_id IS NOT NULL AND a.depth < 15
),
deduped AS (
    SELECT DISTINCT ON (person_id) person_id, depth
    FROM ancestors
    WHERE person_id <> 99993
    ORDER BY person_id, depth
)
SELECT p.id AS ancestor_id, d.depth AS generation, p.given_name, p.surname, p.sex, 
    p.birth_date, p.birth_place, p.death_date, p.death_place, p.burial_place, 
    p.cause_of_death, pf.husband_id AS father_id, pf.wife_id AS mother_id
FROM deduped d
JOIN people p ON p.id = d.person_id
LEFT JOIN family_children pfc ON pfc.child_id = p.id AND pfc.relationship_type = 'BIOLOGICAL'
LEFT JOIN families pf ON pf.id = pfc.family_id
ORDER BY generation, p.id;