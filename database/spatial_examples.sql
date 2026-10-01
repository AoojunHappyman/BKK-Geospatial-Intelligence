-- Boundary-safe assignment: a point on a boundary can intersect more than one district.
-- The ETL only assigns a unique ST_Covers match; ambiguous points remain explicitly flagged.
SELECT p.name,d.district_code,ST_Within(p.geometry,d.geometry) AS strictly_inside,
 ST_Contains(d.geometry,p.geometry) AS district_contains,
 ST_Intersects(d.geometry,p.geometry) AS intersects
FROM point_location p JOIN district d ON ST_Intersects(d.geometry,p.geometry)
LIMIT 20;

-- Example public location near Siam, distance in meters using geography.
SELECT name,ST_Distance(geometry::geography,ST_SetSRID(ST_MakePoint(100.534,13.746),4326)::geography) AS distance_m
FROM healthcare_facility
WHERE ST_DWithin(geometry::geography,ST_SetSRID(ST_MakePoint(100.534,13.746),4326)::geography,3000)
ORDER BY distance_m;

