# Methodology and limitations

District codes 1001–1050 are the canonical join keys. Thai and English names are display attributes. Boundary name ราษฏร์บูรณะ is normalized to ราษฎร์บูรณะ for district 1024. Original raw files are preserved.

## Spatial processing

- Validate and normalize the 50 polygons; never treat longitude/latitude degrees as metres.
- Store EPSG:4326. Compute area and 800 m buffers in UTM 47N, EPSG:32647.
- Assign points using `ST_Covers`. A point must match exactly one polygon; zero matches are outside/unassigned, multiple matches are flagged ambiguous rather than counted twice. Boundary points are included by Covers; `ST_Within` would exclude boundary points.
- Keep 43 transit records outside Bangkok for coverage near district edges. Of 195 accepted station-line records, 152 match Bangkok districts; all 69 health centers and 737 historical flood points match exactly one district.
- Dissolve overlapping station buffers before intersecting district polygons, preventing double-counting.
- Simplify boundary geometry by 15 m only for the map response. Calculations use original validated geometry.
- Nearby API uses `ST_DWithin` and `ST_Distance` on geography in metres. See `database/spatial_examples.sql` for executable spatial examples.

## Map context and annotations

The Chao Phraya overlay is a cached OpenStreetMap **river centerline**, not a riverbank polygon, navigational chart or flood-risk input. No external tile server is required. Its query, SHA256 and retrieval timestamp are in `frontend/public/context/source.json`; the original response is an immutable raw snapshot. Refresh it explicitly with `python scripts/fetch_river_context.py`. OpenStreetMap ODbL attribution is displayed on the map. A full street basemap is not part of this change.

District label anchors come from PostGIS `ST_PointOnSurface`, ensuring the label is inside its district rather than using a centroid that can fall outside concave polygons. Thai text is shaped locally by the browser and rendered as high-resolution, white-halo sprites in a MapLibre symbol layer, with collision avoidance and a minimum zoom of 9. More labels become visible as users zoom in.

Tooltip comparisons use the **unweighted arithmetic mean of districts with non-null values** for the selected metric. They show absolute differences in the metric's unit (percentage points for percent-valued metrics), not a population-weighted city measure. Missing values are excluded and the denominator is visible. Zero remains a measured value; no-data has a separate gray swatch. Fit Bangkok changes only the camera, retaining the selected district and comparison set.

## Metric definitions

| Metric | Formula / interpretation |
|---|---|
| Registered population | DOPA district population, December 2025 |
| Population density | registered population / polygon area km² |
| Age 60+ share | age 60+ / Thai population classified by age × 100 |
| Transit station count | distinct source station-line records with Status=1 located inside district |
| Transit proximity | area(district ∩ union of 800 m station buffers) / district area × 100 |
| Public health centers | number of BMA public health center records inside district |
| Centers per 100k | center count / December 2025 registered population × 100,000 |
| Flood locations | count of points from BMA 2022 flood lessons dataset |

Population totals 5,422,568, while the Thai age-classified denominator is 5,280,172. The remaining 142,396 belong to separately reported source categories and are not silently included in age shares. Age 60+ totals 1,305,293. See `data/README.md` for reconciliation.

The polygon area sum is about 1,583.2631 km² and need not equal published administrative area statistics. Transit proximity describes land area, not reachable population, station entrances, walking time or service frequency. Interchange stations can have multiple line records. OSM supplies 55 missing coordinates only when a unique station node has the exact DRT reference; source/node IDs are retained.

Health data covers BMA public health centers, not all hospitals or clinics, and has no confirmed survey year. Population is registered population, not actual daytime or resident population. Flood points describe historical reports, not present hazard probabilities. A count of zero means no records in that dataset, not safety. Missing datasets produce null values; zero is used only when the relevant source is present.

Datasets are from different dates. Rankings are computed from a selected metric and are not a quality score. No weighted composite, ML, travel-time model or trend inference is included in this MVP.
