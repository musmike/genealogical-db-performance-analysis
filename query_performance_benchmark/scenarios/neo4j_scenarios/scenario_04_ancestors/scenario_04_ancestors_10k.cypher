// Scenario 04: Ancestor Retrieval
// Retrieves all distinct biological ancestors of a selected individual
// up to a configured depth (10 generations for 10k).
// Uses the individual identified in summary.txt as having the most ancestors.
// Should return the columns in the following order and with the following names:
// ancestor_id, generation (distance from the starting individual), given_name, surname,
// sex, birth_date, birth_place, marriage_date, marriage_place,
// death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
// Orders the results first by generation ascending, then by ancestor_id ascending within each generation.
// NOTE: marriage_date and marriage_place should correspond to the marriage with the ancestor
//       that is in the lineage, not any other marriage that the ancestor may have had
//       with someone who is not part of the ancestry.
// NOTE: father_id and mother_id should be populated for all returned ancestors
//       except those in the last generation being returned (i.e., the most distant ancestors in the result set).

MATCH (start:Person {id: 9833})

MATCH path = (start)
              ((:Person)<-[c:HAS_CHILD WHERE c.relationshipType = 'BIOLOGICAL']-(:Family)<-[:HUSBAND_OF|WIFE_OF]-(:Person)){1,10}
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