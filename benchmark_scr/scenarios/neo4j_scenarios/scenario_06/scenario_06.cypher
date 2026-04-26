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

MATCH (p:Person)-[:HUSBAND_OF|WIFE_OF]->(f:Family)-[:HAS_BIOLOGICAL_CHILD]->(c:Person)
WHERE p.birthDate IS NOT NULL AND c.birthDate IS NOT NULL

WITH p, c, duration.inDays(p.birthDate, c.birthDate).days AS ageDiff
WITH min(ageDiff) AS minDiff, collect({p: p, c: c, ageDiff: ageDiff}) AS allPairs

UNWIND [pair IN allPairs WHERE pair.ageDiff = minDiff] AS winner

WITH winner.p AS p, winner.c AS c, minDiff AS age_difference_in_days, 
     duration.between(winner.p.birthDate, winner.c.birthDate).years AS age_at_first_child
RETURN 
      p.id                    AS parent_id, 
      p.givenName             AS given_name, 
      p.surname               AS surname, 
      p.sex                   AS sex, 
      p.birthDate             AS birth_date, 
      p.birthPlace            AS birth_place, 
      age_at_first_child      AS age_at_first_child, 
      age_difference_in_days  AS age_difference_in_days, 
      c.id                    AS child_id, 
      c.birthDate             AS child_birth_date, 
      c.birthPlace            AS child_birth_place
ORDER BY parent_id ASC, child_id ASC;
