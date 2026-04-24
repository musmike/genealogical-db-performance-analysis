-- Scenario 08: Insert Family
-- Benchmarks inserting two biological parents and one sibling
-- for the selected person.
-- Uses an adopted individual with no biological parents as the anchor,
-- as identified in expected_results/scenario_08_09_insert_delete.txt, to avoid FK/graph integrity complications.


-- RECOMMENDED PARAMETERS: Adopted Anchor Person ID = 135

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, 
    birth_place, death_date, death_place, cause_of_death, burial_place, occupation)
VALUES
    (20001, 'Jan',  'Kowalski', 'M', true, '1372-06-15', 'Kraków', '1437-11-02', 
    'Kraków', 'Old age', 'Cemetery in Kraków', 'Farmer'),
    (20002, 'Anna', 'Kowalska', 'F', true, '1375-03-22', 'Kraków', '1445-01-10', 
    'Kraków', 'Fever', 'Cemetery in Kraków', 'Weaver');

INSERT INTO families (id, status, marriage_date, marriage_place, husband_id, wife_id)
VALUES (20001, 'MARRIED', '1394-05-10', 'Kraków', 20001, 20002);

-- Adopted individual
INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (20001, 135, 'BIOLOGICAL');

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, 
birth_place, death_date, death_place, cause_of_death, burial_place, occupation)
VALUES (20003, 'Piotr', 'Kowalski', 'M', true, '1405-09-01', 'Kraków', '1435-04-12', 
    'Kraków', 'Accident', 'Cemetery in Kraków', 'Blacksmith');

INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (20001, 20003, 'BIOLOGICAL');