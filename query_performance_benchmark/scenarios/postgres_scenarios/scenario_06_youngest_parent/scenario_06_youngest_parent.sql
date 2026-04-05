-- Scenario 06: Youngest Parent
-- Identifies the individual who had their first biological child
-- at the youngest age (calculated in days), considering both male and female parents.
-- Traversal follows biological links only.
-- Should return the columns in the following order and with the following names:
-- parent_id, given_name, surname, sex, birth_date, birth_place, age_at_first_child, age_difference_in_days,
-- child_id, child_birth_date, child_birth_place
-- Orders the results by parent_id ascending and then child_id ascending.
-- More than one individual may be returned if multiple parents had their first child
-- at the same youngest age or if there are multiple children born to the same parent at the same age (e.g., twins).

WITH family_members AS (
    SELECT id AS family_id, husband_id AS parent_id
    FROM families
    WHERE husband_id IS NOT NULL
    UNION ALL
    SELECT id AS family_id, wife_id AS parent_id
    FROM families
    WHERE wife_id IS NOT NULL
),

parent_child AS (
    SELECT p.id AS parent_id, p.given_name, p.surname, p.sex, p.birth_date AS parent_birth_date, 
        p.birth_place AS parent_birth_place, c.id AS child_id, c.birth_date AS child_birth_date, 
        c.birth_place AS child_birth_place, (c.birth_date - p.birth_date) AS age_diff_days
    FROM people p
    JOIN family_members fm ON fm.parent_id = p.id
    JOIN family_children fc ON fc.family_id = fm.family_id AND fc.relationship_type = 'BIOLOGICAL'
    JOIN people c ON c.id = fc.child_id
    WHERE p.birth_date IS NOT NULL AND c.birth_date IS NOT NULL
),

min_age AS (
    SELECT MIN(age_diff_days) AS min_days
    FROM parent_child
)

SELECT pc.parent_id, pc.given_name, pc.surname, pc.sex, pc.parent_birth_date AS birth_date, 
    pc.parent_birth_place AS birth_place, EXTRACT(YEAR FROM AGE(pc.child_birth_date, 
    pc.parent_birth_date))::int AS age_at_first_child, pc.age_diff_days AS age_difference_in_days, 
    pc.child_id, pc.child_birth_date, pc.child_birth_place
FROM parent_child pc
JOIN min_age m ON pc.age_diff_days = m.min_days
ORDER BY pc.parent_id, pc.child_id;