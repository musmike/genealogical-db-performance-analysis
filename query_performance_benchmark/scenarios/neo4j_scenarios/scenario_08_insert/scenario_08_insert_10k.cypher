// Scenario 08: Insert Family
// Benchmarks inserting two biological parents and one sibling
// for the selected person.
// Uses an adopted individual with no biological parents as the anchor,
// as identified in expected_results/scenario_08_09_insert_delete.txt, to avoid FK/graph integrity complications.


// RECOMMENDED PARAMETERS: Adopted Anchor Person ID = 267

CREATE (:Person {id: 20001, givenName: 'Jan', surname: 'Kowalski', sex: 'M', isDeceased: true, birthDate: date('1471-06-15'), birthPlace: 'Kraków', deathDate: date('1536-11-02'), deathPlace: 'Kraków', causeOfDeath: 'Old age', burialPlace: 'Cemetery in Kraków', occupation: 'Farmer'});
CREATE (:Person {id: 20002, givenName: 'Anna', surname: 'Kowalska', sex: 'F', isDeceased: true, birthDate: date('1474-03-22'), birthPlace: 'Kraków', deathDate: date('1544-01-10'), deathPlace: 'Kraków', causeOfDeath: 'Fever', burialPlace: 'Cemetery in Kraków', occupation: 'Weaver'});

MATCH (father:Person {id: 20001}), (mother:Person {id: 20002})
CREATE (f:Family {id: 20001, status: 'MARRIED', marriageDate: date('1493-05-10'), marriagePlace: 'Kraków'})
CREATE (father)-[:HUSBAND_OF]->(f)
CREATE (mother)-[:WIFE_OF]->(f);

MATCH (f:Family {id: 20001}), (adopted:Person {id: 267})
CREATE (f)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(adopted);

CREATE (:Person {id: 20003, givenName: 'Piotr', surname: 'Kowalski', sex: 'M', isDeceased: true, birthDate: date('1504-09-01'), birthPlace: 'Kraków', deathDate: date('1534-04-12'), deathPlace: 'Kraków', causeOfDeath: 'Accident', burialPlace: 'Cemetery in Kraków', occupation: 'Blacksmith'});

MATCH (f:Family {id: 20001}), (sibling:Person {id: 20003})
CREATE (f)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(sibling);