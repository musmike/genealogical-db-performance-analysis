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
UNWIND replacements AS pair
WITH n, pair
WHERE n.birthPlace = pair[0]
   OR n.deathPlace = pair[0]
   OR n.burialPlace = pair[0]

SET
  n.birthPlace = CASE WHEN n.birthPlace = pair[0] THEN pair[1] ELSE n.birthPlace END,
  n.deathPlace = CASE WHEN n.deathPlace = pair[0] THEN pair[1] ELSE n.deathPlace END

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
UNWIND replacements AS pair
WITH n, pair
WHERE n.marriagePlace = pair[0]

SET
  n.marriagePlace = pair[1]

RETURN n;