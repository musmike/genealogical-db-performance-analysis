// Scenario 04: Ancestor Retrieval
// Retrieves all distinct biological ancestors of a selected individual
// up to a configured depth (10 generations for 10k).
// Uses the individual identified in summary.txt as having the most ancestors.

MATCH (start:Person {id: 9833})

MATCH path = (start)
              ((:Person)<-[:child]-(:Family)<-[:husband|wife]-(:Person)){1,10}
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