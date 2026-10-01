-- Metric values are rebuilt from source tables inside the ETL transaction.
DROP MATERIALIZED VIEW IF EXISTS district_metrics;
CREATE MATERIALIZED VIEW district_metrics AS
WITH areas AS (
 SELECT district_code, ST_Area(ST_Transform(geometry,32647))/1000000.0 AS area_km2 FROM district
), buffers AS (
 -- Stations outside Bangkok remain available so border districts include nearby service.
 SELECT ST_UnaryUnion(ST_Collect(ST_Buffer(ST_Transform(geometry,32647),800))) AS geom
 FROM point_location WHERE kind='transit'
), counts AS (
 SELECT district_code,
 count(*) FILTER(WHERE kind='transit')::int AS transit_station_count,
 count(*) FILTER(WHERE kind='healthcare')::int AS healthcare_facility_count,
 count(*) FILTER(WHERE kind='risk')::int AS risk_location_count
 FROM point_location GROUP BY district_code
)
SELECT d.district_code,d.name_th,d.name_en,z.zone,to_char(p.reference_period,'YYYY-MM') AS reference_period,
 a.area_km2,p.population_total,p.male_population,p.female_population,
 p.population_total/a.area_km2 AS population_density,
 p.age_0_14,p.age_15_59,p.age_60_plus,p.age_classified_total,p.outside_age_series,
 100.0*p.age_60_plus/NULLIF(p.age_classified_total,0) AS older_share,
 CASE WHEN EXISTS(SELECT 1 FROM data_source WHERE source_id='transit') THEN coalesce(c.transit_station_count,0) END AS transit_station_count,
 CASE WHEN EXISTS(SELECT 1 FROM data_source WHERE source_id='healthcare') THEN coalesce(c.healthcare_facility_count,0) END AS healthcare_facility_count,
 CASE WHEN EXISTS(SELECT 1 FROM data_source WHERE source_id='healthcare') THEN 100000.0*coalesce(c.healthcare_facility_count,0)/NULLIF(p.population_total,0) END AS healthcare_per_100k,
 CASE WHEN EXISTS(SELECT 1 FROM data_source WHERE source_id='risk') THEN coalesce(c.risk_location_count,0) END AS risk_location_count,
 CASE WHEN EXISTS(SELECT 1 FROM data_source WHERE source_id='transit') THEN
 coalesce(100.0*ST_Area(ST_Intersection(ST_Transform(d.geometry,32647),b.geom))/(a.area_km2*1000000.0),0) END AS transit_coverage,
 now() AS updated_at
FROM district d JOIN areas a USING(district_code) JOIN population p USING(district_code)
JOIN district_zone z USING(district_code)
LEFT JOIN counts c USING(district_code) CROSS JOIN buffers b;
CREATE UNIQUE INDEX district_metrics_key ON district_metrics(district_code,reference_period);

