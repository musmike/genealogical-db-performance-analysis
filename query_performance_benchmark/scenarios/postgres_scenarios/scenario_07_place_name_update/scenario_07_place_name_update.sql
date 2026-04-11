-- Scenario 07: Place Name Update
-- Updates all occurrences of historical German city names to their
-- modern Polish equivalents across people (birth_place, death_place)
-- and families (marriage_place). Only full-field matches are replaced, not substrings.
-- Affected names: Posen→Poznań, Danzig→Gdańsk, Breslau→Wrocław,
-- Stettin→Szczecin, Bromberg→Bydgoszcz, Thorn→Toruń.

update people
set
	birth_place = CASE birth_place
    WHEN 'Posen' THEN 'Poznań'
    WHEN 'Danzig' THEN 'Gdańsk'
    WHEN 'Breslau' THEN 'Wrocław'
    WHEN 'Stettin' THEN 'Szczecin'
    WHEN 'Bromberg' THEN 'Bydgoszcz'
    WHEN 'Thorn' THEN 'Toruń'
    ELSE birth_place
  END,

  death_place = CASE death_place
    WHEN 'Posen' THEN 'Poznań'
    WHEN 'Danzig' THEN 'Gdańsk'
    WHEN 'Breslau' THEN 'Wrocław'
    WHEN 'Stettin' THEN 'Szczecin'
    WHEN 'Bromberg' THEN 'Bydgoszcz'
    WHEN 'Thorn' THEN 'Toruń'
    ELSE death_place
  END
        
WHERE
  birth_place IN ('Posen','Danzig','Breslau','Stettin','Bromberg','Thorn') OR
  death_place IN ('Posen','Danzig','Breslau','Stettin','Bromberg','Thorn');


update families
SET marriage_place = CASE marriage_place
  WHEN 'Posen' THEN 'Poznań'
  WHEN 'Danzig' THEN 'Gdańsk'
  WHEN 'Breslau' THEN 'Wrocław'
  WHEN 'Stettin' THEN 'Szczecin'
  WHEN 'Bromberg' THEN 'Bydgoszcz'
  WHEN 'Thorn' THEN 'Toruń'
  ELSE marriage_place
END
WHERE marriage_place IN ('Posen','Danzig','Breslau','Stettin','Bromberg','Thorn');