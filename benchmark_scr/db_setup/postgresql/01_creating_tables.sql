DROP TABLE IF EXISTS family_children, families, people;

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
    status          VARCHAR(20),    -- e.g., 'MARRIED', 'DIVORCED', 'WIDOWED'
    marriage_date   DATE,
    marriage_place  VARCHAR(100),
    husband_id      INTEGER,
    wife_id         INTEGER,

    CONSTRAINT at_least_one_parent CHECK (
        husband_id IS NOT NULL OR wife_id IS NOT NULL
    ),
    CONSTRAINT fk_families_husband FOREIGN KEY (husband_id)
        REFERENCES people(id),
    CONSTRAINT fk_families_wife FOREIGN KEY (wife_id)
        REFERENCES people(id)
);

CREATE TABLE IF NOT EXISTS family_children (
    family_id           INTEGER         NOT NULL,
    child_id            INTEGER         NOT NULL,
    relationship_type   VARCHAR(20)     NOT NULL,   -- e.g., 'BIOLOGICAL', 'ADOPTED', 'FOSTER'

    CONSTRAINT pk_family_children PRIMARY KEY (family_id, child_id),
    CONSTRAINT fk_fc_family FOREIGN KEY (family_id)
        REFERENCES families(id) ON DELETE CASCADE,
    CONSTRAINT fk_fc_child FOREIGN KEY (child_id)
        REFERENCES people(id) ON DELETE CASCADE
);
