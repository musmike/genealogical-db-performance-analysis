COPY people FROM '/data/10k/postgres/people.csv' CSV HEADER;
COPY families FROM '/data/10k/postgres/families.csv' CSV HEADER;
COPY family_children FROM '/data/10k/postgres/family_children.csv' CSV HEADER;