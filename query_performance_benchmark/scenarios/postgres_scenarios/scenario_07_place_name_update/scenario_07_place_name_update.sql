-- Scenario 07: Place Name Update
-- Updates all occurrences of historical German city names to their
-- modern Polish equivalents across people (birth_place, death_place)
-- and families (marriage_place). Only full-field matches are replaced, not substrings.
-- Affected names: Posen→Poznań, Danzig→Gdańsk, Breslau→Wrocław,
-- Stettin→Szczecin, Bromberg→Bydgoszcz, Thorn→Toruń.

update people
set
	birth_place = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(birth_place,
        'Posen','Poznań'),
        'Danzig','Gdańsk'),
        'Breslau','Wrocław'),
        'Stettin','Szczecin'),
        'Bromberg','Bydgoszcz'),
        'Thorn','Toruń'),
        
    death_place = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(death_place,
        'Posen','Poznań'),
        'Danzig','Gdańsk'),
        'Breslau','Wrocław'),
        'Stettin','Szczecin'),
        'Bromberg','Bydgoszcz'),
        'Thorn','Toruń'),
    burial_place = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(burial_place,
        'Posen','Poznań'),
        'Danzig','Gdańsk'),
        'Breslau','Wrocław'),
        'Stettin','Szczecin'),
        'Bromberg','Bydgoszcz'),
        'Thorn','Toruń')
        
where
	birth_place ~ '(Posen|Danzig|Breslau|Stettin|Bromberg|Thorn)' OR
	death_place ~ '(Posen|Danzig|Breslau|Stettin|Bromberg|Thorn)' OR
	burial_place ~ '(Posen|Danzig|Breslau|Stettin|Bromberg|Thorn)';


UPDATE families
SET marriage_place = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(marriage_place,
        'Posen','Poznań'),
        'Danzig','Gdańsk'),
        'Breslau','Wrocław'),
        'Stettin','Szczecin'),
        'Bromberg','Bydgoszcz'),
        'Thorn','Toruń')
WHERE 
    marriage_place ~ '(Posen|Danzig|Breslau|Stettin|Bromberg|Thorn)';