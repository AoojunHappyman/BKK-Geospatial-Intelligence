CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS schema_migration(version integer PRIMARY KEY, applied_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS data_source (
 source_id text PRIMARY KEY, name text NOT NULL, organization text NOT NULL,
 url text NOT NULL, retrieved_at timestamptz NOT NULL, last_updated text,
 reference_period text, license text, raw_format text NOT NULL,
 sha256 text NOT NULL, raw_path text NOT NULL, notes text NOT NULL,
 row_count integer NOT NULL CHECK(row_count >= 0)
);
CREATE TABLE IF NOT EXISTS district (
 district_code text PRIMARY KEY CHECK(district_code ~ '^10[0-9]{2}$'),
 name_th text NOT NULL UNIQUE, name_en text NOT NULL,
 geometry geometry(MultiPolygon,4326) NOT NULL,
 source_id text NOT NULL REFERENCES data_source,
 CHECK(ST_IsValid(geometry)), CHECK(NOT ST_IsEmpty(geometry))
);
CREATE INDEX IF NOT EXISTS district_geometry_idx ON district USING gist(geometry);
CREATE TABLE IF NOT EXISTS population (
 district_code text REFERENCES district, reference_period date NOT NULL,
 population_total integer NOT NULL CHECK(population_total>=0),
 male_population integer NOT NULL CHECK(male_population>=0),
 female_population integer NOT NULL CHECK(female_population>=0),
 age_0_14 integer NOT NULL, age_15_59 integer NOT NULL, age_60_plus integer NOT NULL,
 age_classified_total integer NOT NULL, outside_age_series integer NOT NULL,
 source_id text NOT NULL REFERENCES data_source,
 PRIMARY KEY(district_code,reference_period),
 CHECK(male_population+female_population=population_total),
 CHECK(age_0_14+age_15_59+age_60_plus=age_classified_total),
 CHECK(age_classified_total+outside_age_series=population_total)
);
CREATE TABLE IF NOT EXISTS point_location (
 source_id text REFERENCES data_source, source_record_id text,
 kind text NOT NULL CHECK(kind IN ('transit','healthcare','risk')),
 name text NOT NULL, category text NOT NULL,
 geometry geometry(Point,4326) NOT NULL,
 district_code text REFERENCES district,
 assignment_status text NOT NULL DEFAULT 'pending',
 properties jsonb NOT NULL DEFAULT '{}',
 PRIMARY KEY(source_id,source_record_id), CHECK(ST_IsValid(geometry))
);
CREATE INDEX IF NOT EXISTS point_geometry_idx ON point_location USING gist(geometry);
CREATE INDEX IF NOT EXISTS point_geography_idx ON point_location USING gist((geometry::geography));
CREATE INDEX IF NOT EXISTS point_district_kind_idx ON point_location(district_code,kind);
CREATE TABLE IF NOT EXISTS etl_run (
 run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 completed_at timestamptz DEFAULT now(), report jsonb NOT NULL
);
CREATE OR REPLACE VIEW transit_station AS SELECT * FROM point_location WHERE kind='transit';
CREATE OR REPLACE VIEW healthcare_facility AS SELECT * FROM point_location WHERE kind='healthcare';
CREATE OR REPLACE VIEW risk_location AS SELECT * FROM point_location WHERE kind='risk';
INSERT INTO schema_migration(version) VALUES(1) ON CONFLICT DO NOTHING;

