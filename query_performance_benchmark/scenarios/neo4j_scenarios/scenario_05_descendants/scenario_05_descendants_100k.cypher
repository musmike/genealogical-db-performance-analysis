// Scenario 05: Descendant Retrieval
// Retrieves all distinct biological descendants of a selected individual
// up to a configured depth (10 generations for 100k).
// Uses the individual identified in summary.txt as having the most descendants.
// Should return the columns in the following order and with the following names:
// descendant_id, generation (distance from the starting individual), given_name, surname,
// sex, birth_date, birth_place, death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
// Orders the results first by generation ascending, then by descendant_id ascending within each generation.
// NOTE: father_id and mother_id should be populated only if the parent leads to the starting individual (progenitor) in the lineage.


MATCH (start:Person {id: 59218})

MATCH path = (start)
             (
               (par)-[:HUSBAND_OF|WIFE_OF]->(:Family)
               -[r:HAS_CHILD WHERE r.relationshipType = 'BIOLOGICAL']->()
             ){1, 10}
             (desc:Person)

WITH desc,
     collect({gen: length(path) / 2, parent: last(par)}) AS candidates

WITH desc,
     reduce(best = head(candidates), c IN candidates |
       CASE WHEN c.gen < best.gen THEN c ELSE best END
     ) AS shortest

RETURN
    desc.id              AS descendant_id,
    shortest.gen         AS generation,
    desc.givenName       AS given_name,
    desc.surname         AS surname,
    desc.sex             AS sex,
    desc.birthDate       AS birth_date,
    desc.birthPlace      AS birth_place,
    desc.deathDate       AS death_date,
    desc.deathPlace      AS death_place,
    desc.burialPlace     AS burial_place,
    desc.causeOfDeath    AS cause_of_death,
    shortest.parent.id   AS parent_id

ORDER BY generation, desc.id;