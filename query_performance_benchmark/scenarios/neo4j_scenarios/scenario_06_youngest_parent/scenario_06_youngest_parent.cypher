// Scenario 06: Youngest Parent
// Identifies the individual who had their first biological child
// at the youngest age. Traversal follows biological links only.

MATCH (f:family)-[:child]->(c:person)
MATCH (p:person)-[:wife|husband]->(f)

WITH c, p,
     duration.inDays(date(p.birthDate), date(c.birthDate)).days AS ageDiff

ORDER BY ageDiff ASC
LIMIT 1

RETURN c AS child,
       p AS parent,
       ageDiff AS ageDifferenceInDays;