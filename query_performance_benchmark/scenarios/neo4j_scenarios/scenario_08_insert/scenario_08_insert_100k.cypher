// Scenario 08: Insert Family
// Benchmarks inserting two biological parents and one sibling
// for the selected person.
// Uses an adopted individual with no biological parents as the anchor,
// as identified in summary.txt, to avoid FK/graph integrity complications

CREATE (:Person {id: 200001, givenName: 'Jan',  surname: 'Kowalski', sex: 'M', isDeceased: false, birthDate: date('0875-06-15'), birthPlace: 'Kraków'});
CREATE (:Person {id: 200002, givenName: 'Anna', surname: 'Kowalska', sex: 'F', isDeceased: false, birthDate: date('0878-03-22'), birthPlace: 'Kraków'});

MATCH (father:Person {id: 200001}), (mother:Person {id: 200002})
CREATE (f:Family {id: 200001, status: 'MARRIED', marriageDate: date('0900-05-10'), marriagePlace: 'Kraków'})
CREATE (father)-[:HUSBAND_OF]->(f)
CREATE (mother)-[:WIFE_OF]->(f);

MATCH (f:Family {id: 200001}), (adopted:Person {id: 2105})
CREATE (f)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(adopted);

CREATE (:Person {id: 200003, givenName: 'Piotr', surname: 'Kowalski', sex: 'M', isDeceased: false, birthDate: date('0903-09-01'), birthPlace: 'Kraków'});

MATCH (f:Family {id: 200001}), (sibling:Person {id: 200003})
CREATE (f)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(sibling);