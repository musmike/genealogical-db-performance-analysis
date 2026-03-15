-- Upward traversal (ancestors / LCA)
CREATE INDEX idx_fc_child_id ON family_children(child_id);
-- CREATE INDEX idx_fam_id ON families(id); -- Not needed as id is the primary key and thus already indexed

-- Downward traversal (descendants / LCA)
CREATE INDEX idx_fam_husband ON families(husband_id);
CREATE INDEX idx_fam_wife ON families(wife_id);
CREATE INDEX idx_fc_family_id ON family_children(family_id);


-- Filtering/aggregating scenarios
CREATE INDEX idx_ppl_surname ON people(surname);
CREATE INDEX idx_ppl_birth_date ON people(birth_date);
CREATE INDEX idx_ppl_birth_place ON people(birth_place);


-- Place name update
-- CREATE INDEX idx_ppl_birth_place ON people(birth_place); -- Created above
CREATE INDEX idx_fam_marriage_place ON families(marriage_place);
CREATE INDEX idx_ppl_death_place ON people(death_place);
CREATE INDEX idx_ppl_burial_place ON people(burial_place);
