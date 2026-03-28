DO $$
DECLARE
  t_start TIMESTAMP;
  t_end   TIMESTAMP;
  ms      NUMERIC;
BEGIN
  t_start := clock_timestamp();

  COPY people          FROM '/data/100k/postgres/people.csv'          CSV HEADER;
  COPY families        FROM '/data/100k/postgres/families.csv'        CSV HEADER;
  COPY family_children FROM '/data/100k/postgres/family_children.csv' CSV HEADER;

  t_end := clock_timestamp();

  ms := EXTRACT(EPOCH FROM (t_end - t_start)) * 1000;

  -- Output the import time in milliseconds for use in the benchmark
  RAISE NOTICE 'POSTGRES_IMPORT_MS=%', ms::BIGINT;
END;
$$;