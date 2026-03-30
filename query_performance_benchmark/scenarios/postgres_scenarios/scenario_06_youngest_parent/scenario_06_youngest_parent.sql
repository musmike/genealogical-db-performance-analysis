-- Scenario 06: Youngest Parent
-- Identifies the individual who had their first biological child
-- at the youngest age (calculated in days), considering both male and female parents.
-- Traversal follows biological links only.
-- Should return the columns in the following order and with the following names:
-- parent_id, given_name, surname, sex, birth_date, birth_place, age_at_first_child, age_difference_in_days,
-- child_id, child_birth_date, child_birth_place
-- Orders the results by parent_id ascending.
-- More than one individual may be returned if multiple parents had their first child
-- at the same youngest age.

WITH family_members AS (
    SELECT id AS family_id, husband_id AS person_id FROM families WHERE husband_id IS NOT NULL
    UNION ALL
    SELECT id AS family_id, wife_id    AS person_id FROM families WHERE wife_id    IS NOT NULL
),

parent_first AS (
    SELECT p.id AS parent_id, p.given_name, p.surname, p.sex,
           p.birth_date                                                     AS parent_birth_date,
           MIN(child.birth_date)                                            AS first_child_birth_date,
           EXTRACT(YEAR FROM AGE(MIN(child.birth_date), p.birth_date))::int AS age_at_first_child
    FROM people p
    JOIN family_members  fm    ON fm.person_id = p.id
    JOIN family_children fc    ON fc.family_id = fm.family_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN people          child ON child.id     = fc.child_id
    WHERE p.birth_date IS NOT NULL AND child.birth_date IS NOT NULL
    GROUP BY p.id, p.given_name, p.surname, p.sex, p.birth_date
),

youngest AS (
    SELECT MIN(age_at_first_child) AS youngest_age FROM parent_first
),

first_child AS (
    SELECT DISTINCT ON (pf.parent_id)
           pf.parent_id, c.given_name AS child_given_name, c.surname AS child_surname, c.sex AS child_sex, c.birth_date AS child_birth_date
    FROM parent_first    pf
    JOIN youngest        y  ON y.youngest_age = pf.age_at_first_child
    JOIN family_members  fm ON fm.person_id   = pf.parent_id
    JOIN family_children fc ON fc.family_id   = fm.family_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN people          c  ON c.id           = fc.child_id  AND c.birth_date         = pf.first_child_birth_date
    ORDER BY pf.parent_id, c.id
)

SELECT pf.parent_id, pf.given_name, pf.surname, pf.sex,
       pf.parent_birth_date, pf.age_at_first_child,
       fc.child_given_name, fc.child_surname, fc.child_sex, fc.child_birth_date
FROM parent_first pf
JOIN youngest    y  ON y.youngest_age = pf.age_at_first_child
JOIN first_child fc ON fc.parent_id   = pf.parent_id
ORDER BY pf.parent_id;