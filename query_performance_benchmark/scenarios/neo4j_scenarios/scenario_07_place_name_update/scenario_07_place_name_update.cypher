// Scenario 07: Place Name Update
// Updates all occurrences of historical German city names to their
// modern Polish equivalents across people (birth_place, death_place, burial_place)
// and families (marriage_place). Match is substring-based
// Affected names: Posen→Poznań, Danzig→Gdańsk, Breslau→Wrocław,
// Stettin→Szczecin, Bromberg→Bydgoszcz, Thorn→Toruń.

with {Posen:'Poznań', Danzig:'Gdańsk', Breslau:'Wrocław', Stettin:'Szczecin',Bromberg:'Bydgoszcz',Thorn:'Toruń'} as map
MATCH(n:person)
SET
  n.birth_place = COALESCE(map[n.birth_place], n.birth_place),
  n.death_place = COALESCE(map[n.death_place], n.death_place),
  n.burial_place = COALESCE(map[n.burial_place], n.burial_place)
RETURN n;

with {Posen:'Poznań', Danzig:'Gdańsk', Breslau:'Wrocław', Stettin:'Szczecin',Bromberg:'Bydgoszcz',Thorn:'Toruń'} as map
MATCH(n:family)
SET
  n.marriage_place = COALESCE(map[n.marriage_place], n.marriage_place)
RETURN n;