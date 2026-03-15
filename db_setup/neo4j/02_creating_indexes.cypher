

// Already indexed by default.
// CREATE INDEX person_id FOR (p:Person) ON (p.personId);
// CREATE INDEX family_id FOR (f:Family) ON (f.familyId);

// Filtering/aggregating scenarios
CREATE INDEX FOR (p:Person) ON (p.surname);
CREATE INDEX FOR (p:Person) ON (p.birthDate);
CREATE INDEX FOR (p:Person) ON (p.birthPlace);

// Place name update
// CREATE INDEX FOR (p:Person) ON (p.birthPlace); -- Created above
CREATE INDEX FOR (f:Family) ON (f.marriagePlace);
CREATE INDEX FOR (p:Person) ON (p.deathPlace);
CREATE INDEX FOR (p:Person) ON (p.burialPlace);


// MATCH (f1:Family)-[:HAS_CHILD]->(p:Person)-[:HUSBAND_OF|WIFE_OF]->(f2:Family) RETURN f1, p, f2 LIMIT 1000;