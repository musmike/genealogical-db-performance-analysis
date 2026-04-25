// Scenario 05: Descendant Retrieval
// Retrieves all distinct biological descendants of a selected individual
// up to a configured depth (5 generations for 1k).
// Uses the individual identified in expected_results/scenario_05_descendants_1k.txt as having the most descendants.
// Should return the columns in the following order and with the following names:
// descendant_id, generation (the shortest path length from the starting individual), given_name, surname,
// sex, birth_date, birth_place, death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
// Orders the results first by generation ascending, then by descendant_id ascending within each generation.


// RECOMMENDED PARAMETERS: Person ID = 26

MATCH (start:Person {id: 26})

MATCH path = (start)
              ((:Person)-[:HUSBAND_OF|WIFE_OF]->
              (:Family)-[:HAS_BIOLOGICAL_CHILD]->(:Person)){1,5}
              (des:Person)
WITH des, min(length(path)) / 2 AS gen

OPTIONAL MATCH (f:Family)-[:HAS_BIOLOGICAL_CHILD]->(des)
OPTIONAL MATCH (father:Person)-[:HUSBAND_OF]->(f)
OPTIONAL MATCH (mother:Person)-[:WIFE_OF]->(f)

RETURN 
    des.id             AS descendant_id, 
    gen                AS generation, 
    des.givenName      AS given_name, 
    des.surname        AS surname, 
    des.sex            AS sex, 
    des.birthDate      AS birth_date, 
    des.birthPlace     AS birth_place, 
    des.deathDate      AS death_date, 
    des.deathPlace     AS death_place, 
    des.burialPlace    AS burial_place, 
    des.causeOfDeath   AS cause_of_death, 
    father.id          AS father_id, 
    mother.id          AS mother_id
ORDER BY generation ASC, descendant_id ASC;
