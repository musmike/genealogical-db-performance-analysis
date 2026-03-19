// Scenario 01: Lowest Common Ancestor (LCA)
// Finds the closest common biological ancestor of two selected individuals.
// The specific pair of person IDs is taken from summary.txt (LCA section) —
// chosen such that the total path length through the LCA matches the
// configured target (16 hops for 100k dataset).
// Traversal follows biological relationships only (adopted/foster excluded).

MATCH pA = SHORTEST 1 PATHS (startA:Person {id: 93074})
  ((:Person)<-[rA:HAS_CHILD WHERE rA.relationshipType = 'BIOLOGICAL']-(:Family)
   <-[:HUSBAND_OF|WIFE_OF]-(:Person)){0,15}
  (ancA:Person)
WITH ancA, length(pA)/2 AS distA
WITH collect(ancA)                            AS nodesA,
     collect({node: ancA, dist: distA})       AS ancDataA

MATCH pB = SHORTEST 1 PATHS (startB:Person {id: 96276})
  ((:Person)<-[rB:HAS_CHILD WHERE rB.relationshipType = 'BIOLOGICAL']-(:Family)
   <-[:HUSBAND_OF|WIFE_OF]-(:Person)){0,15}
  (ancB:Person)
WHERE ancB IN nodesA
WITH ancDataA, ancB, length(pB)/2 AS distB,
     [x IN ancDataA WHERE x.node = ancB | x.dist][0] AS distA

WITH ancB, distA, distB, distA + distB AS total_dist
WITH min(total_dist) AS minTotal,
     collect({anc: ancB, distA: distA, distB: distB, total: total_dist}) AS candidates

UNWIND candidates AS c
WITH c WHERE c.total = minTotal

RETURN
  c.anc.id         AS lca_id,
  c.anc.givenName  AS given_name,
  c.anc.surname    AS surname,
  c.anc.birthDate  AS birth_date,
  c.anc.birthPlace AS birth_place,
  c.anc.deathDate  AS death_date,
  c.anc.deathPlace AS death_place,
  c.distA          AS path_length_from_a,
  c.distB          AS path_length_from_b,
  c.total          AS total_dist
ORDER BY lca_id;

