-- Scenario 04: Ancestor Retrieval (10k dataset)
-- Retrieves all distinct biological ancestors of a selected individual
-- up to a configured depth (10 generations in this case).
-- Uses the individual identified in summary.txt as having the most ancestors.

WITH RECURSIVE ancestors(person_id, depth, via_family_id, visited) AS (
    SELECT 9833, 0, NULL::int, ARRAY[9833]
    UNION ALL
    SELECT parent.id, a.depth + 1, f.id, a.visited || parent.id
    FROM ancestors a
    JOIN family_children fc ON fc.child_id = a.person_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN families f ON f.id = fc.family_id
    JOIN people parent ON parent.id IN (f.husband_id, f.wife_id)
    WHERE a.depth < 10
      AND NOT (parent.id = ANY(a.visited))
),
deduped AS (
    SELECT DISTINCT ON (person_id) person_id, depth, via_family_id
    FROM ancestors
    WHERE person_id <> 9833
    ORDER BY person_id, depth
)
SELECT p.id AS ancestor_id, d.depth AS generation,
    p.given_name, p.surname, p.sex, p.birth_date, p.birth_place,
    fm.marriage_date, fm.marriage_place,
    p.death_date, p.death_place, p.burial_place, p.cause_of_death,
    pf.husband_id AS father_id, pf.wife_id AS mother_id
FROM deduped d
JOIN people p ON p.id = d.person_id
LEFT JOIN families fm ON fm.id = d.via_family_id
LEFT JOIN family_children pfc ON pfc.child_id = p.id AND pfc.relationship_type = 'BIOLOGICAL'
LEFT JOIN families pf ON pf.id = pfc.family_id
ORDER BY generation, p.id;
