-- Scenario 05: Descendant Retrieval
-- Retrieves all distinct biological descendants of a selected individual
-- up to a configured depth (10 generations for 100k).
-- Uses the individual identified in expected_results/scenario_05_descendants_100k.txt as having the most descendants.
-- Should return the columns in the following order and with the following names:
-- descendant_id, generation (the shortest path length from the starting individual), given_name, surname,
-- sex, birth_date, birth_place, death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
-- Orders the results first by generation ascending, then by descendant_id ascending within each generation.


-- RECOMMENDED PARAMETERS: Person ID = 21660

WITH RECURSIVE descendants(person_id, depth, via_family_id, visited) AS (
    SELECT 21660, 0, NULL::int, ARRAY[21660]

    UNION ALL

    SELECT child.id, d.depth + 1, f.id, d.visited || child.id
    FROM descendants d
    JOIN families f 
        ON d.person_id IN (f.husband_id, f.wife_id)
    JOIN family_children fc 
        ON fc.family_id = f.id 
       AND fc.relationship_type = 'BIOLOGICAL'
    JOIN people child 
        ON child.id = fc.child_id
    WHERE d.depth < 10
      AND NOT (child.id = ANY(d.visited))
),

deduped AS (
    SELECT DISTINCT ON (person_id) person_id, depth, via_family_id
    FROM descendants
    WHERE person_id <> 21660
    ORDER BY person_id, depth
)

SELECT 
    p.id AS descendant_id,
    d.depth AS generation,
    p.given_name, p.surname, p.sex, p.birth_date, p.birth_place,
    fm.marriage_date, fm.marriage_place,
    p.death_date, p.death_place, p.burial_place, p.cause_of_death,
    pf.husband_id AS father_id, 
    pf.wife_id AS mother_id
FROM deduped d
JOIN people p ON p.id = d.person_id
LEFT JOIN families fm ON fm.id = d.via_family_id
LEFT JOIN family_children pfc 
    ON pfc.child_id = p.id 
   AND pfc.relationship_type = 'BIOLOGICAL'
LEFT JOIN families pf ON pf.id = pfc.family_id
ORDER BY generation, p.id;
