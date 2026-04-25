-- Scenario 05: Descendant Retrieval
-- Retrieves all distinct biological descendants of a selected individual
-- up to a configured depth (17 generations for 100k).
-- Uses the individual identified in expected_results/scenario_05_descendants_100k.txt as having the most descendants.
-- Should return the columns in the following order and with the following names:
-- descendant_id, generation (the shortest path length from the starting individual), given_name, surname,
-- sex, birth_date, birth_place, death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
-- Orders the results first by generation ascending, then by descendant_id ascending within each generation.


-- RECOMMENDED PARAMETERS: Person ID = 12035

WITH RECURSIVE descendants AS (
    SELECT 12035 AS person_id, 0 AS depth

    UNION

    SELECT fc.child_id, d.depth + 1
    FROM descendants d
    JOIN LATERAL (
        SELECT id FROM families WHERE husband_id = d.person_id
        UNION
        SELECT id FROM families WHERE wife_id = d.person_id
    ) f ON true
    JOIN family_children fc ON fc.family_id = f.id AND fc.relationship_type = 'BIOLOGICAL'
    WHERE d.depth < 17
),
deduped AS (
    SELECT DISTINCT ON (person_id) person_id, depth
    FROM descendants
    WHERE person_id <> 12035
    ORDER BY person_id, depth
)
SELECT 
    p.id                AS descendant_id, 
    d.depth             AS generation, 
    p.given_name        AS given_name, 
    p.surname           AS surname, 
    p.sex               AS sex, 
    p.birth_date        AS birth_date, 
    p.birth_place       AS birth_place, 
    p.death_date        AS death_date, 
    p.death_place       AS death_place, 
    p.burial_place      AS burial_place, 
    p.cause_of_death    AS cause_of_death, 
    pf.husband_id       AS father_id,
    pf.wife_id          AS mother_id
FROM deduped d
JOIN people p ON p.id = d.person_id
LEFT JOIN family_children pfc ON pfc.child_id = p.id AND pfc.relationship_type = 'BIOLOGICAL'
LEFT JOIN families pf ON pf.id = pfc.family_id
ORDER BY generation ASC, descendant_id ASC;