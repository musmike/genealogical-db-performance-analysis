-- Scenario 08: Insert Family
-- Benchmarks inserting two biological parents and one sibling
-- for the selected person.
-- Uses an adopted individual with no biological parents as the anchor,
-- as identified in summary.txt, to avoid FK/graph integrity complications.

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, birth_place)
VALUES
    (20001, 'Jan',  'Kowalski', 'M', false, '1575-06-15', 'Kraków'),
    (20002, 'Anna', 'Kowalska', 'F', false, '1578-03-22', 'Kraków');

INSERT INTO families (id, status, marriage_date, marriage_place, husband_id, wife_id)
VALUES (20001, 'MARRIED', '1600-05-10', 'Kraków', 20001, 20002);

INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (20001, 420, 'BIOLOGICAL');

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, birth_place)
VALUES (20003, 'Piotr', 'Kowalski', 'M', false, '1603-09-01', 'Kraków');

INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (20001, 20003, 'BIOLOGICAL');