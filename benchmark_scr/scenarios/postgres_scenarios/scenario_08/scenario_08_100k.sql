-- Scenario 08: Insert Family
-- Benchmarks inserting two biological parents and one sibling
-- for the selected person.
-- Uses an adopted individual with no biological parents as the anchor,
-- as identified in expected_results/scenario_08_09_insert_delete.txt, to avoid FK/graph integrity complications.


-- RECOMMENDED PARAMETERS: Adopted Anchor Person ID = 220

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, 
    birth_place, death_date, death_place, cause_of_death, burial_place, occupation)
VALUES
    (200001, 'Jan',  'Kowalski', 'M', true, '0680-06-15', 'Kraków', '0745-11-02', 
    'Kraków', 'Old age', 'Cemetery in Kraków', 'Farmer'),
    (200002, 'Anna', 'Kowalska', 'F', true, '0683-03-22', 'Kraków', '0753-01-10', 
    'Kraków', 'Fever', 'Cemetery in Kraków', 'Weaver');

INSERT INTO families (id, status, marriage_date, marriage_place, husband_id, wife_id)
VALUES (200001, 'MARRIED', '0702-05-10', 'Kraków', 200001, 200002);

-- Adopted individual
INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (200001, 220, 'BIOLOGICAL');

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, 
    birth_place, death_date, death_place, cause_of_death, burial_place, occupation)
VALUES (200003, 'Piotr', 'Kowalski', 'M', true, '0713-09-01', 'Kraków', '0743-04-12', 
    'Kraków', 'Accident', 'Cemetery in Kraków', 'Blacksmith');

INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (200001, 200003, 'BIOLOGICAL');