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

WITH family_spouses AS (
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
    c.birth_place AS child_birth_place, (c.birth_date - p.birth_date) AS age_diff_days,
    MIN(c.birth_date - p.birth_date) OVER () AS global_min_days
    FROM people p
    JOIN family_spouses fs ON fs.parent_id = p.id
    JOIN family_children fc ON fc.family_id = fs.family_id
        AND fc.relationship_type = 'BIOLOGICAL'
    JOIN people c ON c.id = fc.child_id
    WHERE p.birth_date IS NOT NULL AND c.birth_date IS NOT NULL
)
SELECT 
    parent_id                                                         AS parent_id, 
    given_name                                                        AS given_name, 
    surname                                                           AS surname, 
    sex                                                               AS sex, 
    parent_birth_date                                                 AS birth_date, 
    parent_birth_place                                                AS birth_place, 
    EXTRACT(YEAR FROM AGE(child_birth_date, parent_birth_date))::int  AS age_at_first_child, 
    age_diff_days                                                     AS age_difference_in_days, 
    child_id                                                          AS child_id, 
    child_birth_date                                                  AS child_birth_date, 
    child_birth_place                                                 AS child_birth_place
FROM parent_child
WHERE age_diff_days = global_min_days
ORDER BY parent_id ASC, child_id ASC;