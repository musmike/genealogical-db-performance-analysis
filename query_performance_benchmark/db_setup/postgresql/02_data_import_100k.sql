COPY people FROM '/data/100k/postgres/people.csv' CSV HEADER;
COPY families FROM '/data/100k/postgres/families.csv' CSV HEADER;
COPY family_children FROM '/data/100k/postgres/family_children.csv' CSV HEADER;