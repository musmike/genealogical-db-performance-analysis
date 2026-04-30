#!/bin/bash

docker exec postgres_db psql -q -U user -d benchmarkdb -c "\
CREATE TABLE IF NOT EXISTS people (
    id                INTEGER,
    given_name        VARCHAR(50),
    surname           VARCHAR(50),
    sex               CHAR(1),
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
    id              INTEGER,
    status          VARCHAR(20),    -- e.g., 'MARRIED', 'DIVORCED', 'WIDOWED'
    marriage_date   DATE,
    marriage_place  VARCHAR(100),
    husband_id      INTEGER,
    wife_id         INTEGER
);

CREATE TABLE IF NOT EXISTS family_children (
    family_id           INTEGER,
    child_id            INTEGER,
    relationship_type   VARCHAR(20)  -- e.g., 'BIOLOGICAL', 'ADOPTED', 'FOSTER'
);

COPY people          FROM '/data/1k/postgres/people.csv'          CSV HEADER;
COPY families        FROM '/data/1k/postgres/families.csv'        CSV HEADER;
COPY family_children FROM '/data/1k/postgres/family_children.csv' CSV HEADER;
"