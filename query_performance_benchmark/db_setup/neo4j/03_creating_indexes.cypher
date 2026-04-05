// Scenario 01, 04, 05: lookup for traversal start nodes
CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT family_id_unique IF NOT EXISTS FOR (f:Family) REQUIRE f.id IS UNIQUE;

// Scenario 01, 04, 05: filters BIOLOGICAL links at each traversal step
CREATE INDEX IF NOT EXISTS FOR ()-[r:HAS_CHILD]-() ON (r.relationshipType);

// Scenario 02: surname equality filter
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.surname);

// Scenario 02: composite covers both surname equality and birth year range in one index scan
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.surname, p.birthDate);

// Scenario 03, 06: birth date range filter and age calculation
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.birthDate);

// Scenario 03: birth place grouping / filter
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.birthPlace);