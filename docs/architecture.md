# Architecture and API

Python ETL extracts content-addressed raw snapshots, validates schema, coordinates and stable district codes, then loads a transaction into PostgreSQL/PostGIS. The materialized view is rebuilt within that transaction so readers do not see partly updated metrics. An ETL failure rolls back the database change; reports retain rejected records and assignment counts.

## Database

| Relation | Key / content |
|---|---|
| district | district_code; Thai/English name; MultiPolygon EPSG:4326 |
| population | district_code + reference_period; population and age bands |
| population_age | district_code + reference_period + age_lower; real male/female single-year counts, 101+ open group |
| district_zone | district_code; one of six BMA working groups, with source reference |
| data_source | source_id; URL, organization, reference period, retrieval timestamp, SHA256, notes |
| point_location | kind + source_record_id; Point EPSG:4326, district assignment, source attributes |
| transit_station / healthcare_facility / risk_location | Typed views over point_location |
| district_metrics | Materialized spatial aggregation, one row per district and population period |
| etl_run | Load audit report and timestamp |
| schema_migration | Applied schema version |

GiST indexes cover district/point geometries and point geography. Migration 002 and the ETL load 5,100 single-year age-sex records and validate their sums against each district's age-classified population. The pyramid endpoint groups these into five-year bands and 100+. Only the 2025-12 population period is loaded; the application does not imply a historical time series.

## API

Interactive OpenAPI is served at `/docs`. All frontend analytical requests use `/api`.

| Route | Result |
|---|---|
| `/api/health` | Actual PostGIS connection and district count |
| `/api/metrics` | Definitions, units and source dependencies |
| `/api/benchmarks` | City aggregate ratios and per-district means with explicit methods |
| `/api/districts/{code}/population-pyramid` | Age-sex counts in five-year bands, classified/excluded totals |
| `/api/districts`, `/api/districts/{code}` | District metrics |
| `/api/districts/geojson` | All 50 boundaries, simplified only for display |
| `/api/districts/{code}/population` | Population and age bands |
| `/api/districts/{code}/mobility` | Transit points in district |
| `/api/districts/{code}/infrastructure` | Public health centers in district |
| `/api/districts/{code}/risk` | Historical flood points in district |
| `/api/analytics/{metric}` | Computed descending dense rank; ties share rank |
| `/api/compare?districts=1007,1030` | 2–4 distinct districts in requested order |
| `/api/datasets`, `/api/datasets/{source_id}` | Provenance and caveats |
| `/api/points/{kind}` | Transit/healthcare/risk GeoJSON |
| `/api/nearby?lon=100.53&lat=13.75&radius_m=800` | True PostGIS geography distance query |
| `/api/export/districts.csv?districts=1030,1007` | Optional district subset, preserving the supplied table order; empty selection exports headers only |

Values and identifier inputs are parameterized; metric identifiers are allowlisted. API transactions are read-only with a 15-second statement timeout. Vite proxies API traffic in development; Nginx proxies in Docker. The demo has no authentication and binds published ports to localhost. Public production exposure, access controls and operational monitoring require a separate deployment review.
