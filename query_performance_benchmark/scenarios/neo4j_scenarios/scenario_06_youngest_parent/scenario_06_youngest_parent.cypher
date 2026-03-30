// Scenario 06: Youngest Parent
// Identifies the individual who had their first biological child
// at the youngest age (calculated in days), considering both male and female parents.
// Traversal follows biological links only.
// Should return the columns in the following order and with the following names:
// parent_id, given_name, surname, sex, birth_date, birth_place, age_at_first_child, age_difference_in_days,
// child_id, child_birth_date, child_birth_place
// Orders the results by parent_id ascending.
// More than one individual may be returned if multiple parents had their first child
// at the same youngest age.

MATCH (f:Family)-[:HAS_CHILD]->(c:Person)
MATCH (p:Person)-[:HUSBAND_OF|WIFE_OF]->(f)

WITH c, p,
     duration.inDays(p.birthDate, c.birthDate).days AS ageDiff

WITH min(ageDiff) AS minDiff

MATCH (f:Family)-[:HAS_CHILD]->(c:Person)
MATCH (p:Person)-[:HUSBAND_OF|WIFE_OF]->(f)

WITH c, p,
     duration.inDays(p.birthDate, c.birthDate).days AS ageDiff,
     minDiff

WHERE ageDiff = minDiff

RETURN c.givenName AS child_name,
      c.surname as child_surname,
      c.birthDate as child_birth,
       p.givenName AS parent_name,
      p.surname as parent_surname,
      p.birthDate as parent_birth,
       ageDiff AS ageDifferenceInDays
LIMIT 1;