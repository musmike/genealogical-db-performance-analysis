DROP TABLE IF EXISTS family_children, families, people CASCADE;

CREATE TABLE IF NOT EXISTS people (
    id                INTEGER         PRIMARY KEY,
    given_name        VARCHAR(50),
    surname           VARCHAR(50),
    sex               CHAR(1)         NOT NULL CHECK (sex IN ('M', 'F', 'U')),
    is_deceased       BOOLEAN,
    birth_place       VARCHAR(100),
    birth_date        DATE,
    death_place       VARCHAR(100),
    death_date        DATE,
    cause_of_death    VARCHAR(100),
    burial_place      VARCHAR(100),
    occupation        VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS families (
    id              INTEGER         PRIMARY KEY,
    status          VARCHAR(20),    -- e.g., 'MARIED', 'DIVORCED', 'WIDOWED'
    marriage_date   DATE,
    marriage_place  VARCHAR(100),
    husband_id      INTEGER         REFERENCES people(id),
    wife_id         INTEGER         REFERENCES people(id),

    CHECK (husband_id IS NOT NULL OR wife_id IS NOT NULL)
);


CREATE TABLE IF NOT EXISTS family_children (
    family_id           INTEGER         NOT NULL REFERENCES families(id),
    child_id            INTEGER         NOT NULL REFERENCES people(id),
    relationship_type   VARCHAR(20)     NOT NULL,   -- e.g., 'BIOLOGICAL', 'ADOPTED', 'FOSTER'
    PRIMARY KEY (family_id, child_id)
);
