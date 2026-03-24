// Scenario 06: Youngest Parent
// Identifies the individual who had their first biological child
// at the youngest age. Traversal follows biological links only.

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