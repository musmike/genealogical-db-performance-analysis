// Scenario 04: Ancestor Retrieval (1k dataset)
// Retrieves all distinct biological ancestors of a selected individual
// up to a configured depth (5 generations in this case).
// Uses the individual identified in summary.txt as having the most ancestors.
// Should return the columns in the following order and with the following names:
// ancestor_id, generation (the shortest path length from the starting individual), given_name, surname,
// sex, birth_date, birth_place, death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
// Orders the results first by generation ascending, then by ancestor_id ascending within each generation.

MATCH (start:Person {id: 927})

MATCH path = (start)
              ((:Person)<-[c:HAS_CHILD WHERE c.relationshipType = 'BIOLOGICAL']-(:Family)<-[:HUSBAND_OF|WIFE_OF]-(:Person)){1,5}
              (anc:Person)

WITH anc, length(path)/2 AS generation

WITH anc, min(generation) AS gen

RETURN
    anc.id             AS ancestor_id,
    gen                AS generation,
    anc.givenName      AS given_name,
    anc.surname        AS surname,
    anc.sex            AS sex,
    anc.birthDate      AS birth_date,
    anc.birthPlace     AS birth_place,
    anc.deathDate      AS death_date,
    anc.deathPlace     AS death_place,
    anc.burialPlace    AS burial_place,
    anc.causeOfDeath   AS cause_of_death
ORDER BY generation, ancestor_id;