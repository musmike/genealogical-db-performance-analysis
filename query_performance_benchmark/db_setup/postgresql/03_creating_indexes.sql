-- Scenario 01, 04, 05, 06: downward traversal from parent to family node
CREATE INDEX IF NOT EXISTS idx_fam_husband ON families(husband_id);
CREATE INDEX IF NOT EXISTS idx_fam_wife ON families(wife_id);

-- Scenario 01, 04, 05: upward traversal filtered to BIOLOGICAL children only
-- INCLUDE (family_id) eliminates heap fetch in scenario 04 recursive hot path
CREATE INDEX IF NOT EXISTS idx_fc_child_rel_cov
    ON family_children (child_id, relationship_type)
    INCLUDE (family_id);

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

-- Scenario 03: composite eliminates separate scans for birth_place grouping and birth_date range
CREATE INDEX IF NOT EXISTS idx_ppl_birth_place_date ON people(birth_place, birth_date);

-- Scenario 04: covers id lookup returning husband_id and wife_id without heap fetch
CREATE INDEX IF NOT EXISTS idx_families_id_cov
    ON families (id)
    INCLUDE (husband_id, wife_id);