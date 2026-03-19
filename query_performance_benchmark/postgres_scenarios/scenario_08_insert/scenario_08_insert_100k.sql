-- Scenario 08: Insert Family
-- Benchmarks inserting two biological parents and one sibling
-- for the selected person.
-- Uses an adopted individual with no biological parents as the anchor,
-- as identified in summary.txt, to avoid FK/graph integrity complications.

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, birth_place)
VALUES
    (200001, 'Jan',  'Kowalski', 'M', false, '0875-06-15', 'Kraków'),
    (200002, 'Anna', 'Kowalska', 'F', false, '0878-03-22', 'Kraków');

INSERT INTO families (id, status, marriage_date, marriage_place, husband_id, wife_id)
VALUES (200001, 'MARRIED', '0900-05-10', 'Kraków', 200001, 200002);

INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (200001, 2105, 'BIOLOGICAL');

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, birth_place)
VALUES (200003, 'Piotr', 'Kowalski', 'M', false, '0903-09-01', 'Kraków');

INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (200001, 200003, 'BIOLOGICAL');