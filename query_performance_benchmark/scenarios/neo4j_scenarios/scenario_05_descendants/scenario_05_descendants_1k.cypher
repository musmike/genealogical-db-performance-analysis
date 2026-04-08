// Scenario 05: Descendant Retrieval
// Retrieves all distinct biological descendants of a selected individual
// up to a configured depth (3 generations for 1k).
// Uses the individual identified in expected_results/scenario_05_descendants_1k.txt as having the most descendants.
// Should return the columns in the following order and with the following names:
// descendant_id, generation (the shortest path length from the starting individual), given_name, surname,
// sex, birth_date, birth_place, death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
// Orders the results first by generation ascending, then by descendant_id ascending within each generation.


// RECOMMENDED PARAMETERS: Person ID = 292

MATCH (start:Person {id: 292})

MATCH path = (start)
              ((par)-[:HUSBAND_OF|WIFE_OF]->(:Family)
              -[r:HAS_CHILD WHERE r.relationshipType = 'BIOLOGICAL']->()){1, 3}
              (desc:Person)

WITH desc, MIN(length(path) / 2) AS generation

OPTIONAL MATCH (f:Family)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(desc)
OPTIONAL MATCH (father:Person)-[:HUSBAND_OF]->(f)
OPTIONAL MATCH (mother:Person)-[:WIFE_OF]->(f)

RETURN desc.id AS descendant_id, generation, desc.givenName AS given_name, 
    desc.surname AS surname, desc.sex AS sex, desc.birthDate AS birth_date, 
    desc.birthPlace AS birth_place, desc.deathDate AS death_date, 
    desc.deathPlace AS death_place, desc.burialPlace AS burial_place, 
    desc.causeOfDeath AS cause_of_death, father.id AS father_id, mother.id AS mother_id
ORDER BY generation, desc.id;



