-- Scenario 01, 04, 05: downward traversal from parent to family node
CREATE INDEX IF NOT EXISTS idx_fam_husband ON families(husband_id);
CREATE INDEX IF NOT EXISTS idx_fam_wife    ON families(wife_id);

-- Scenario 01, 04, 05: upward traversal filtered to BIOLOGICAL children only
CREATE INDEX IF NOT EXISTS idx_fc_child_rel  ON family_children(child_id,  relationship_type);

-- Scenario 05, 06: downward traversal filtered to BIOLOGICAL children only
CREATE INDEX IF NOT EXISTS idx_fc_family_rel ON family_children(family_id, relationship_type);

-- Scenario 02: surname equality filter
CREATE INDEX IF NOT EXISTS idx_ppl_surname ON people(surname);

-- Scenario 02: composite covers both surname equality and birth year range in one index scan
CREATE INDEX IF NOT EXISTS idx_ppl_surname_birth ON people(surname, birth_date);

-- Scenario 03, 06: birth date range filter and age calculation
CREATE INDEX IF NOT EXISTS idx_ppl_birth_date ON people(birth_date);

-- Scenario 03: birth place grouping / filter
CREATE INDEX IF NOT EXISTS idx_ppl_birth_place ON people(birth_place);