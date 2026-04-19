// Scenario 08: Insert Family
// Benchmarks inserting two biological parents and one sibling
// for the selected person.
// Uses an adopted individual with no biological parents as the anchor,
// as identified in expected_results/scenario_08_09_insert_delete.txt, to avoid FK/graph integrity complications.


// RECOMMENDED PARAMETERS: Adopted Anchor Person ID = 204

CREATE (:Person {id: 200001, givenName: 'Jan', surname: 'Kowalski', sex: 'M', isDeceased: true, birthDate: date('0671-06-15'), birthPlace: 'Kraków', deathDate: date('0736-11-02'), deathPlace: 'Kraków', causeOfDeath: 'Old age', burialPlace: 'Cemetery in Kraków', occupation: 'Farmer'});
CREATE (:Person {id: 200002, givenName: 'Anna', surname: 'Kowalska', sex: 'F', isDeceased: true, birthDate: date('0674-03-22'), birthPlace: 'Kraków', deathDate: date('0744-01-10'), deathPlace: 'Kraków', causeOfDeath: 'Fever', burialPlace: 'Cemetery in Kraków', occupation: 'Weaver'});

MATCH (father:Person {id: 200001}), (mother:Person {id: 200002})
CREATE (f:Family {id: 200001, status: 'MARRIED', marriageDate: date('0693-05-10'), marriagePlace: 'Kraków'})
CREATE (father)-[:HUSBAND_OF]->(f)
CREATE (mother)-[:WIFE_OF]->(f);

MATCH (f:Family {id: 200001}), (adopted:Person {id: 204})
CREATE (f)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(adopted);

CREATE (:Person {id: 200003, givenName: 'Piotr', surname: 'Kowalski', sex: 'M', isDeceased: true, birthDate: date('0704-09-01'), birthPlace: 'Kraków', deathDate: date('0734-04-12'), deathPlace: 'Kraków', causeOfDeath: 'Accident', burialPlace: 'Cemetery in Kraków', occupation: 'Blacksmith'});

MATCH (f:Family {id: 200001}), (sibling:Person {id: 200003})
CREATE (f)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(sibling);