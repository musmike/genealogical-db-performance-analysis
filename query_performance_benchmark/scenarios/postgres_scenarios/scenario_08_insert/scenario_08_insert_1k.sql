-- Scenario 08: Insert Family
-- Benchmarks inserting two biological parents and one sibling
-- for the selected person.
-- Uses an adopted individual with no biological parents as the anchor,
-- as identified in summary.txt, to avoid FK/graph integrity complications.

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, birth_place)
VALUES
    (2001, 'Jan',   'Kowalski', 'M', false, '1775-06-15', 'Kraków'),
    (2002, 'Anna',  'Kowalska', 'F', false, '1778-03-22', 'Kraków');

INSERT INTO families (id, status, marriage_date, marriage_place, husband_id, wife_id)
VALUES (2001, 'MARRIED', '1800-05-10', 'Kraków', 2001, 2002);

INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (2001, 169, 'BIOLOGICAL');

INSERT INTO people (id, given_name, surname, sex, is_deceased, birth_date, birth_place)
VALUES  (2003, 'Piotr', 'Kowalski', 'M', false, '1803-09-01', 'Kraków');

INSERT INTO family_children (family_id, child_id, relationship_type)
VALUES (2001, 2003, 'BIOLOGICAL');