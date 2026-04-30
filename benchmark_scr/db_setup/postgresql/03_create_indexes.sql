--- 1. Constraints for table 'people' ---
ALTER TABLE people ADD PRIMARY KEY (id);

ALTER TABLE people ALTER COLUMN sex SET NOT NULL;

ALTER TABLE people ADD CONSTRAINT check_sex CHECK (sex IN ('M', 'F', 'U'));

--- 2. Constraints for table 'families' ---
ALTER TABLE families ADD PRIMARY KEY (id);

ALTER TABLE families ADD CONSTRAINT at_least_one_parent CHECK (
    husband_id IS NOT NULL OR wife_id IS NOT NULL
);
ALTER TABLE families ADD CONSTRAINT fk_families_husband FOREIGN KEY (husband_id)
    REFERENCES people(id);
ALTER TABLE families ADD CONSTRAINT fk_families_wife FOREIGN KEY (wife_id)
    REFERENCES people(id);

--- 3. Constraints for table 'family_children' ---
ALTER TABLE family_children ADD CONSTRAINT pk_family_children PRIMARY KEY (family_id, child_id);

ALTER TABLE family_children ALTER COLUMN family_id SET NOT NULL;
ALTER TABLE family_children ALTER COLUMN child_id SET NOT NULL;
ALTER TABLE family_children ALTER COLUMN relationship_type SET NOT NULL;

ALTER TABLE family_children ADD CONSTRAINT fk_fc_family FOREIGN KEY (family_id)
    REFERENCES families(id) ON DELETE CASCADE;
ALTER TABLE family_children ADD CONSTRAINT fk_fc_child FOREIGN KEY (child_id)
    REFERENCES people(id) ON DELETE CASCADE;


-- ============================================================
-- Scenario 01: Lowest Common Ancestor (LCA)
-- ============================================================

-- Already covered by PK (people_pkey)
-- CREATE INDEX IF NOT EXISTS idx_ppl_id ON people(id); 

CREATE UNIQUE INDEX IF NOT EXISTS idx_fc_child_bio_cov ON family_children(child_id)
INCLUDE (family_id)
WHERE relationship_type = 'BIOLOGICAL';

CREATE INDEX IF NOT EXISTS idx_families_id_cov ON families(id)
INCLUDE (husband_id, wife_id);


-- ============================================================
-- Scenario 02: Surname and Birth Year Filter
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_ppl_surname_birthdate ON people(surname, birth_date);


-- ============================================================
-- Scenario 03: Births per City per Quarter-Century
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_ppl_birthplace_birthdate ON people(birth_place, birth_date);


-- ============================================================
-- Scenario 04: Ancestor Retrieval
-- ============================================================

-- Already covered by PK (people_pkey)
-- CREATE INDEX IF NOT EXISTS idx_ppl_id ON people(id);

-- Already covered by idx_fc_child_bio_cov (Scenario 01)
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_fc_child_bio_cov ON family_children(child_id)
-- INCLUDE (family_id)
-- WHERE relationship_type = 'BIOLOGICAL';

-- Already covered by idx_families_id_cov (Scenario 01)
-- CREATE INDEX IF NOT EXISTS idx_families_id_cov ON families(id)
-- INCLUDE (husband_id, wife_id);


-- ============================================================
-- Scenario 05: Descendant Retrieval
-- ============================================================

-- Already covered by PK (people_pkey)
-- CREATE INDEX IF NOT EXISTS idx_ppl_id ON people(id);

-- Already covered by idx_fc_child_bio_cov (Scenario 01)
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_fc_child_bio_cov ON family_children(child_id)
-- INCLUDE (family_id)
-- WHERE relationship_type = 'BIOLOGICAL';

-- Already covered by idx_families_id_cov (Scenario 01)
-- CREATE INDEX IF NOT EXISTS idx_families_id_cov ON families(id)
-- INCLUDE (husband_id, wife_id);

CREATE INDEX IF NOT EXISTS idx_families_husband ON families(husband_id);

CREATE INDEX IF NOT EXISTS idx_families_wife ON families(wife_id);

CREATE INDEX IF NOT EXISTS idx_fc_family_bio_cov ON family_children(family_id)
INCLUDE (child_id)
WHERE relationship_type = 'BIOLOGICAL';


-- ============================================================
-- Scenario 06: Youngest Parent
-- ============================================================

-- Already covered by idx_fc_family_bio_cov (Scenario 05)
-- CREATE INDEX IF NOT EXISTS idx_fc_family_bio_cov ON family_children(family_id)
-- INCLUDE (child_id)
-- WHERE relationship_type = 'BIOLOGICAL';

-- Already covered by idx_families_husband in (Scenario 05)
-- CREATE INDEX IF NOT EXISTS idx_families_husband ON families(husband_id);

-- Already covered by idx_families_wife (Scenario 05)
-- CREATE INDEX IF NOT EXISTS idx_families_wife ON families(wife_id);

-- Already covered by PK (people_pkey)
-- CREATE INDEX IF NOT EXISTS idx_ppl_id ON people(id);


-- ============================================================
-- Scenario 07: Place Name Update
-- ============================================================

-- No additional indexes needed.


-- ============================================================
-- Scenario 08: Insert Family
-- ============================================================

-- No additional indexes needed.


-- ============================================================
-- Scenario 09: Delete Family
-- ============================================================

-- Already covered by PK (families_pkey) and idx_families_id_cov (Scenario 01)
-- CREATE INDEX IF NOT EXISTS idx_families_id ON families(id);
-- CREATE INDEX IF NOT EXISTS idx_families_id_cov ON families(id)
-- INCLUDE (husband_id, wife_id);

-- Already covered by leading column of pk_family_children (family_id):
-- CREATE INDEX IF NOT EXISTS idx_fc_family ON family_children(family_id);

-- Already covered by PK (people_pkey)
-- CREATE INDEX IF NOT EXISTS idx_ppl_id ON people(id);

CREATE INDEX IF NOT EXISTS idx_fc_child ON family_children(child_id);