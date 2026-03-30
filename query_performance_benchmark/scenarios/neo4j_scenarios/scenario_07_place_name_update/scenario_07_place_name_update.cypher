// Scenario 07: Place Name Update
// Updates all occurrences of historical German city names to their
// modern Polish equivalents across people (birth_place, death_place)
// and families (marriage_place). Only full-field matches are replaced, not substrings.
// Affected names: Posen→Poznań, Danzig→Gdańsk, Breslau→Wrocław,
// Stettin→Szczecin, Bromberg→Bydgoszcz, Thorn→Toruń.

WITH [
  ['Posen','Poznań'],
  ['Danzig','Gdańsk'],
  ['Breslau','Wrocław'],
  ['Stettin','Szczecin'],
  ['Bromberg','Bydgoszcz'],
  ['Thorn','Toruń']
] AS replacements

MATCH (n:Person)
WHERE any(pair IN replacements WHERE
  n.birthPlace CONTAINS pair[0] OR
  n.deathPlace CONTAINS pair[0] OR
  n.burialPlace CONTAINS pair[0]
)

SET
  n.birthPlace =
    reduce(val = n.birthPlace, pair IN replacements |
      replace(val, pair[0], pair[1])),

  n.deathPlace =
    reduce(val = n.deathPlace, pair IN replacements |
      replace(val, pair[0], pair[1])),

  n.burialPlace =
    reduce(val = n.burialPlace, pair IN replacements |
      replace(val, pair[0], pair[1]))

RETURN n;

WITH [
  ['Posen','Poznań'],
  ['Danzig','Gdańsk'],
  ['Breslau','Wrocław'],
  ['Stettin','Szczecin'],
  ['Bromberg','Bydgoszcz'],
  ['Thorn','Toruń']
] AS replacements

MATCH (n:Family)
WHERE any(pair IN replacements WHERE
  n.marriagePlace CONTAINS pair[0]
)

SET
  n.marriagePlace =
    reduce(val = n.marriagePlace, pair IN replacements |
      replace(val, pair[0], pair[1]))

RETURN n;