// Scenario 08: Insert Family
// Benchmarks inserting two biological parents and one sibling
// for the selected person.
// Uses an adopted individual with no biological parents as the anchor,
// as identified in summary.txt, to avoid FK/graph integrity complications

CREATE (:Person {id: 20001, givenName: 'Jan',  surname: 'Kowalski', sex: 'M', isDeceased: false, birthDate: date('1575-06-15'), birthPlace: 'Kraków'});
CREATE (:Person {id: 20002, givenName: 'Anna', surname: 'Kowalska', sex: 'F', isDeceased: false, birthDate: date('1578-03-22'), birthPlace: 'Kraków'});

MATCH (father:Person {id: 20001}), (mother:Person {id: 20002})
CREATE (f:Family {id: 20001, status: 'MARRIED', marriageDate: date('1600-05-10'), marriagePlace: 'Kraków'})
CREATE (father)-[:HUSBAND_OF]->(f)
CREATE (mother)-[:WIFE_OF]->(f);

MATCH (f:Family {id: 20001}), (adopted:Person {id: 420})
CREATE (f)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(adopted);

CREATE (:Person {id: 20003, givenName: 'Piotr', surname: 'Kowalski', sex: 'M', isDeceased: false, birthDate: date('1603-09-01'), birthPlace: 'Kraków'});

MATCH (f:Family {id: 20001}), (sibling:Person {id: 20003})
CREATE (f)-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]->(sibling);