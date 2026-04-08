// Scenario 01: Lowest Common Ancestor (LCA)
// Finds the closest common biological ancestor of two selected individuals.
// The specific pair of person IDs is taken from expected_results/scenario_01_lca_100k.txt —
// chosen such that the total path length through the LCA matches the
// configured target (16 hops for 100k dataset).
// Traversal follows biological relationships only (adopted/foster excluded).
// Should return the columns in the following order and with the following names:
// lca_id, given_name, surname, sex, birth_date, birth_place, death_date, death_place, path_length_from_a, path_length_from_b, total_dist.
// Orders the results by lca_id ascending.


// RECOMMENDED PARAMETERS: Person A = 92308, Person B = 96653

MATCH (startNode:Person) 
WHERE startNode.id IN [92308, 96653]
MATCH p = SHORTEST 1 PATHS (startNode)
    ((:Person)<-[:HAS_CHILD {relationshipType: 'BIOLOGICAL'}]-(:Family)
    <-[:HUSBAND_OF|WIFE_OF]-()){0,15}(anc:Person)
WITH anc, startNode.id AS sId, length(p)/2 AS dist
WITH anc,
     min(CASE WHEN sId=92308 THEN dist END) AS distA,
     min(CASE WHEN sId=96653 THEN dist END) AS distB
WHERE distA IS NOT NULL AND distB IS NOT NULL
WITH anc, distA, distB, distA+distB AS total_dist
WITH min(total_dist) AS minTotal, 
     collect({anc:anc, distA:distA, distB:distB, total:total_dist}) AS candidates
UNWIND candidates AS c
WITH c WHERE c.total = minTotal
RETURN c.anc.id AS lca_id, c.anc.givenName AS given_name, c.anc.surname AS surname, 
       c.anc.sex AS sex, c.anc.birthDate AS birth_date, c.anc.birthPlace AS birth_place, 
       c.anc.deathDate AS death_date, c.anc.deathPlace AS death_place, 
       c.distA AS path_length_from_a, c.distB AS path_length_from_b, c.total AS total_dist
ORDER BY lca_id;