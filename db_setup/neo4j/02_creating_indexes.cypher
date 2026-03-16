

// Already indexed by default.
// CREATE INDEX person_id FOR (p:Person) ON (p.id);
// CREATE INDEX family_id FOR (f:Family) ON (f.id);

// Filtering/aggregating scenarios
CREATE INDEX FOR (p:Person) ON (p.surname);
CREATE INDEX FOR (p:Person) ON (p.birthDate);
CREATE INDEX FOR (p:Person) ON (p.birthPlace);

// Place name update
// CREATE INDEX FOR (p:Person) ON (p.birthPlace); -- Created above
CREATE INDEX FOR (f:Family) ON (f.marriagePlace);
CREATE INDEX FOR (p:Person) ON (p.deathPlace);
CREATE INDEX FOR (p:Person) ON (p.burialPlace);