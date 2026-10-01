CREATE TABLE IF NOT EXISTS district_zone (
 district_code text PRIMARY KEY REFERENCES district,
 zone text NOT NULL,
 source_id text NOT NULL REFERENCES data_source
);
CREATE TABLE IF NOT EXISTS population_age (
 district_code text NOT NULL, reference_period date NOT NULL,
 age_lower integer NOT NULL CHECK(age_lower BETWEEN 0 AND 101),
 age_upper integer, male integer NOT NULL CHECK(male>=0), female integer NOT NULL CHECK(female>=0),
 source_id text NOT NULL REFERENCES data_source,
 PRIMARY KEY(district_code, reference_period, age_lower),
 FOREIGN KEY(district_code,reference_period) REFERENCES population,
 CHECK(age_upper>=age_lower OR (age_lower=101 AND age_upper IS NULL))
);
INSERT INTO schema_migration(version) VALUES(2) ON CONFLICT DO NOTHING;
