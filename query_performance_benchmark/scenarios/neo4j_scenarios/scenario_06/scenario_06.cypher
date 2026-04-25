// Scenario 06: Youngest Parent
// Identifies the individual who had their first biological child
// at the youngest age (calculated in days), considering both male and female parents.
// Traversal follows biological links only.
// Should return the columns in the following order and with the following names:
// parent_id, given_name, surname, sex, birth_date, birth_place, age_at_first_child, age_difference_in_days,
// child_id, child_birth_date, child_birth_place
// Orders the results by parent_id ascending and then child_id ascending.
// More than one individual may be returned if multiple parents had their first child
// at the same youngest age or if there are multiple children born to the same parent at the same age (e.g., twins).

MATCH (f:Family)-[r:HAS_CHILD WHERE r.relationshipType = 'BIOLOGICAL']->(c:Person)
MATCH (p:Person)-[:HUSBAND_OF|WIFE_OF]->(f)

WITH c, p,
     duration.inDays(p.birthDate, c.birthDate).days AS ageDiff

WITH min(ageDiff) AS minDiff

MATCH (f:Family)-[:HAS_CHILD]->(c:Person)
MATCH (p:Person)-[:HUSBAND_OF|WIFE_OF]->(f)

WITH c, p,
     duration.inDays(p.birthDate, c.birthDate).days AS ageDiff,
     duration.between(p.birthDate, c.birthDate).years AS ageYears,
     minDiff

WHERE ageDiff = minDiff

RETURN p.id AS parent_id,
      p.givenName as given_name,
      p.surname as surname,
      p.sex as sex,
      p.birthDate as birth_date,
      p.birthPlace as birth_place,
      ageYears as age_at_first_child,
      ageDiff AS age_difference_in_days,
      c.id as child_id,
      c.birthDate as child_birth_date,
      c.birthPlace as child_birth_place
ORDER BY
p.id ASC,
c.id ASC
;