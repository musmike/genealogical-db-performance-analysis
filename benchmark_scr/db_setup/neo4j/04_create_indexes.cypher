// Constraints for the node "Person"
CREATE CONSTRAINT person_sex_required IF NOT EXISTS FOR (p:Person) REQUIRE p.sex IS NOT NULL;


// ============================================================
// Scenario 01: Lowest Common Ancestor (LCA)
// ============================================================

CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;


// ============================================================
// Scenario 02: Surname and Birth Year Filter
// ============================================================

CREATE INDEX person_surname_birthdate IF NOT EXISTS FOR (p:Person) ON (p.surname, p.birthDate);


// ============================================================
// Scenario 03: Births per City per Quarter-Century
// ============================================================

CREATE INDEX idx_person_place_birthdate IF NOT EXISTS FOR (p:Person) ON (p.birthPlace, p.birthDate);


// ============================================================
// Scenario 04: Ancestor Retrieval
// ============================================================

// Already covered by person_id_unique (Scenario 01)
// CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;


// ============================================================
// Scenario 05: Descendant Retrieval
// ============================================================

// Already covered by person_id_unique (Scenario 01)
// CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;


// ============================================================
// Scenario 06: Youngest Parent
// ============================================================

// No additional indexes needed.


// ============================================================
// Scenario 07: Place Name Update
// ============================================================

// No additional indexes needed.


// ============================================================
// Scenario 08: Insert Family
// ============================================================

// No additional indexes needed.


// ============================================================
// Scenario 09: Delete Family
// ============================================================

CREATE CONSTRAINT family_id_unique IF NOT EXISTS FOR (f:Family) REQUIRE f.id IS UNIQUE;

// Already covered by person_id_unique (Scenario 01)
// CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;