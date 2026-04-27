// Scenario 07: Place Name Update
// Updates all occurrences of historical German city names to their
// modern Polish equivalents across people (birth_place, death_place)
// and families (marriage_place). Only full-field matches are replaced, not substrings.
// Affected names: Posen→Poznań, Danzig→Gdańsk, Breslau→Wrocław,
// Stettin→Szczecin, Bromberg→Bydgoszcz, Thorn→Toruń.

WITH {`Poznań`: 'Posen', `Gdańsk`: 'Danzig', `Wrocław`: 'Breslau', 
    `Szczecin`: 'Stettin', `Bydgoszcz`: 'Bromberg', `Toruń`: 'Thorn'} AS pairs
MATCH (p:Person) 
WHERE p.birthPlace IN keys(pairs) 
SET p.birthPlace = pairs[p.birthPlace];

WITH {`Poznań`: 'Posen', `Gdańsk`: 'Danzig', `Wrocław`: 'Breslau', 
    `Szczecin`: 'Stettin', `Bydgoszcz`: 'Bromberg', `Toruń`: 'Thorn'} AS pairs
MATCH (p:Person) 
WHERE p.deathPlace IN keys(pairs) 
SET p.deathPlace = pairs[p.deathPlace];

WITH {`Poznań`: 'Posen', `Gdańsk`: 'Danzig', `Wrocław`: 'Breslau', 
    `Szczecin`: 'Stettin', `Bydgoszcz`: 'Bromberg', `Toruń`: 'Thorn'} AS pairs
MATCH (f:Family) 
WHERE f.marriagePlace IN keys(pairs) 
SET f.marriagePlace = pairs[f.marriagePlace];