// Scenario 04: Ancestor Retrieval
// Retrieves all distinct biological ancestors of a selected individual
// up to a configured depth (15 generations for 100k).
// Uses the individual identified in summary.txt as having the most ancestors.


MATCH (start:Person {id: 99993})

MATCH path = (start)
              ((:Person)<-[c:HAS_CHILD WHERE c.relationshipType = 'BIOLOGICAL']-(:Family)<-[:HUSBAND_OF|WIFE_OF]-(:Person)){1,15}
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