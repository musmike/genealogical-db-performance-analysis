// Scenario 04: Ancestor Retrieval (100k dataset)
// Retrieves all distinct biological ancestors of a selected individual
// up to a configured depth (15 generations in this case).
// Uses the individual identified in summary.txt as having the most ancestors.
// Should return the columns in the following order and with the following names:
// ancestor_id, generation (the shortest path length from the starting individual), given_name, surname,
// sex, birth_date, birth_place, marriage_date, marriage_place, death_date, death_place, burial_place, cause_of_death, father_id, mother_id.
// Orders the results first by generation ascending, then by ancestor_id ascending within each generation.
// NOTE: marriage_date and marriage_place should correspond to the marriage that connects this ancestor 
//       to the specific parent-child lineage of the selected individual, 
//       not any other marriage the ancestor may have had, even if with someone else in the ancestry tree.
// Note: An ancestor may appear more than once in the results if they occupy different generations
//       or are associated with different marriages to other ancestors of the selected individual within THIS family tree. 
//       Their own parents (earlier generations) should only appear again if some of their column values differ 
//       (for example, if they appear in a different generation or with a different marriage). 
//       This ensures all relevant ancestral paths of the selected individual are captured without unnecessary duplicates.

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