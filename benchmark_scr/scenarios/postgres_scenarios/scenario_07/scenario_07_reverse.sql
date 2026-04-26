-- Scenario 07: Place Name Update
-- Updates all occurrences of historical German city names to their
-- modern Polish equivalents across people (birth_place, death_place)
-- and families (marriage_place). Only full-field matches are replaced, not substrings.
-- Affected names: Posen→Poznań, Danzig→Gdańsk, Breslau→Wrocław,
-- Stettin→Szczecin, Bromberg→Bydgoszcz, Thorn→Toruń.

UPDATE people
SET 
    birth_place = CASE birth_place
        WHEN 'Poznań' THEN 'Posen'
        WHEN 'Gdańsk' THEN 'Danzig'
        WHEN 'Wrocław' THEN 'Breslau'
        WHEN 'Szczecin' THEN 'Stettin'
        WHEN 'Bydgoszcz' THEN 'Bromberg'
        WHEN 'Toruń' THEN 'Thorn'
        ELSE birth_place
    END,
    death_place = CASE death_place
        WHEN 'Poznań' THEN 'Posen'
        WHEN 'Gdańsk' THEN 'Danzig'
        WHEN 'Wrocław' THEN 'Breslau'
        WHEN 'Szczecin' THEN 'Stettin'
        WHEN 'Bydgoszcz' THEN 'Bromberg'
        WHEN 'Toruń' THEN 'Thorn'
        ELSE death_place
    END
WHERE birth_place IN ('Poznań','Gdańsk','Wrocław','Szczecin','Bydgoszcz','Toruń') 
    OR death_place IN ('Poznań','Gdańsk','Wrocław','Szczecin','Bydgoszcz','Toruń');

UPDATE families
SET marriage_place = CASE marriage_place
    WHEN 'Poznań' THEN 'Posen'
    WHEN 'Gdańsk' THEN 'Danzig'
    WHEN 'Wrocław' THEN 'Breslau'
    WHEN 'Szczecin' THEN 'Stettin'
    WHEN 'Bydgoszcz' THEN 'Bromberg'
    WHEN 'Toruń' THEN 'Thorn'
    ELSE marriage_place
END
WHERE marriage_place IN ('Poznań','Gdańsk','Wrocław','Szczecin','Bydgoszcz','Toruń');