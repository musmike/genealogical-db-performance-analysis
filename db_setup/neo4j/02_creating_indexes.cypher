

// ID indexes
CREATE INDEX person_id IF NOT EXISTS FOR (p:Person) ON (p.id);
CREATE INDEX family_id IF NOT EXISTS FOR (f:Family) ON (f.id);
CREATE INDEX IF NOT EXISTS FOR ()-[r:HAS_CHILD]-() ON (r.relationshipType);

// Filtering/aggregating scenarios
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.surname);
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.birthDate);
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.birthPlace);

// Place-related indexes
CREATE INDEX IF NOT EXISTS FOR (f:Family) ON (f.marriagePlace);
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.deathPlace);
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.burialPlace);
CREATE INDEX ON :Person(id);