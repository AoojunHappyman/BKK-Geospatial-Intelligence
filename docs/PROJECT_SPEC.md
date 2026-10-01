1. Project Goal
Build BKK Geospatial Intelligence, an interactive urban analytics platform for comparing and exploring all 50 Bangkok districts using real geospatial and public datasets.
The project must demonstrate more than map visualization. It should show an end-to-end workflow covering:
- Data ingestion
- Data cleaning and validation
- Geospatial transformation
- Spatial joins
- PostgreSQL/PostGIS storage
- Spatial SQL
- Backend API development
- District-level analytics
- Interactive geospatial visualization
- Reproducible deployment
Primary analytical dimensions for V1:
1. Demographics — population, area, population density
2. Mobility — public transit stations/accessibility
3. Infrastructure — healthcare/public facilities
4. Urban Risk — accidents, risk locations, or another reliable Bangkok risk dataset
The central analytical unit is always the district.
2. Core Product Principle
Every dataset should ultimately be connected to a Bangkok district.
Bangkok
   |
   +-- Bang Kapi
   +-- Chatuchak
   +-- Pathum Wan
   +-- Lat Krabang
   +-- ...
   +-- 50 districts
For point datasets that do not contain a district name, determine their district using a spatial join against district polygons.
Example:
Healthcare facility
(latitude, longitude)
        |
        v
      POINT
        |
        v
PostGIS ST_Within / ST_Intersects
        |
        v
District polygon
        |
        v
   "Pathum Wan"
3. Data Requirements
Use real public/open data wherever possible. Bangkok Open Data should be a primary source.
Minimum datasets:
- Bangkok 50-district administrative boundaries
- Population by district
- Public transit locations
- Healthcare/public facility locations
- At least one urban-risk dataset
Store source metadata for every dataset:
- Dataset name
- Source organization
- Source URL
- Retrieved date
- Last updated date if available
- License if available
- Raw file format
Important constraints
- Do not fabricate production statistics.
- Do not hardcode district metrics.
- Do not hardcode rankings.
- Clearly distinguish raw values, calculated metrics, and model/score outputs.
- Preserve raw source data separately from processed data.
- Design the pipeline so datasets can be refreshed later.
4. System Architecture
                  DATA SOURCES

        Bangkok Open Data / Open APIs
                     |
        +------------+------------+
        |            |            |
        v            v            v
   Population     Transit      Facilities
        |            |            |
        +------------+------------+
                     |
                     v
                 Python ETL
              Pandas / GeoPandas
                     |
                     v
               Data Validation
                     |
                     v
            PostgreSQL + PostGIS
                     |
              Spatial Analysis
                     |
          +----------+----------+
          |                     |
          v                     v
    Aggregations            Spatial SQL
          |                     |
          +----------+----------+
                     |
                     v
                  FastAPI
                     |
                     v
            React + TypeScript
                     |
                     v
               MapLibre GL
                     |
                     v
          BKK Geospatial Intelligence
The frontend must consume data through the API. It should not directly load analytical CSV files for production features.
5. Technology Stack
Frontend
- React
- TypeScript
- MapLibre GL JS
- A lightweight charting library where needed
- Responsive CSS solution of choice
Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy or another clean PostgreSQL integration
Data Engineering
- Python
- Pandas
- GeoPandas
- Shapely where required
Database
- PostgreSQL
- PostGIS
DevOps
- Docker
- Docker Compose
- GitHub Actions for basic CI
Do not add technologies merely to make the stack larger. Prefer a maintainable architecture.
6. Database Design
Use district as the central/master spatial entity.
district
district_id
district_code
name_th
name_en
area_km2
geometry
geometry must use an appropriate PostGIS polygon/multipolygon type and SRID.
Suggested supporting entities:
district
   |
   +-- population
   +-- transit_station
   +-- healthcare_facility
   +-- risk_location / accident
   +-- district_metrics
   +-- data_source
population
Suggested fields:
population_id
district_id
year
population_total
male_population
female_population
source_id
Only include fields actually supported by the source data.
transit_station
station_id
name
system
latitude
longitude
geometry
district_id
source_id
healthcare_facility
facility_id
name
facility_type
latitude
longitude
geometry
district_id
source_id
district_metrics
This can hold materialized/derived district-level metrics for fast API responses.
district_id
year
population
area_km2
population_density
transit_station_count
healthcare_facility_count
healthcare_per_100k
risk_location_count
updated_at
Do not store derived values if they cannot be reproduced from source data and documented formulas.
7. ETL Pipeline
The data pipeline must be a first-class component of the project.
EXTRACT
   |
   v
Download CSV / GeoJSON / KML / API data
   |
   v
TRANSFORM
   |
   +-- Normalize column names
   +-- Remove duplicates
   +-- Handle missing values
   +-- Standardize district names/codes
   +-- Convert coordinates
   +-- Normalize CRS
   +-- Validate geometry
   |
   v
SPATIAL TRANSFORM
   |
   +-- Point -> district spatial join
   +-- Polygon validation
   +-- Spatial aggregation
   |
   v
LOAD
   |
   v
PostgreSQL / PostGIS
   |
   v
AGGREGATE
   |
   v
district_metrics
Suggested pipeline layout:
data-pipeline/
├── extract/
│   ├── districts.py
│   ├── population.py
│   ├── transit.py
│   ├── healthcare.py
│   └── risk.py
├── transform/
│   ├── districts.py
│   ├── population.py
│   ├── spatial.py
│   └── validation.py
├── load/
│   └── postgres.py
├── config/
│   └── sources.yaml
└── pipeline.py
A developer should eventually be able to run something similar to:
python pipeline.py
and execute the documented ETL workflow.
8. Spatial Analysis Requirements
The project must demonstrate actual PostGIS/geospatial operations rather than using PostGIS only as storage.
Use appropriate functions such as:
ST_Within
ST_Contains
ST_Intersects
ST_DWithin
ST_Area
ST_Distance
Potential examples:
- Determine which district contains a station/facility.
- Count facilities within each district.
- Calculate district area correctly using an appropriate projected CRS/geography approach.
- Find facilities within a distance of a location.
- Compare accessibility across districts.
Document CRS decisions and avoid calculating real-world distance/area incorrectly from unprojected coordinates.
9. Frontend Pages
Build five primary product areas.
9.1 Overview — /
Purpose: introduce the platform and provide a city-wide snapshot.
Suggested layout:
BKK GEOSPATIAL INTELLIGENCE
Bangkok Urban Data at District Level

+----------+ +------------+ +----------+ +-------------+
|    50    | | Population | | Transit  | | Facilities  |
| Districts| |    ...     | |   ...    | |    ...      |
+----------+ +------------+ +----------+ +-------------+

              [ BANGKOK MAP ]

Layer:
[ Population ] [ Mobility ] [ Infrastructure ] [ Risk ]
Requirements:
- Render all 50 district polygons.
- Hover -> district name + basic metric.
- Click -> navigate/open district profile.
- Switch analytical layers.
- Include source/update information.
9.2 District Explorer — /districts
This is one of the hero features.
Allow users to choose a metric such as:
Population Density
Transit Accessibility
Healthcare Coverage
Urban Risk
Display the selected metric as a district-level choropleth.
Requirements:
- Metric selector
- Choropleth legend
- Hover tooltip
- District search
- Metric distribution/ranking view
- Data source information
Rankings must be calculated from real API data, never hardcoded.
9.3 District Profile — /district/:id
Example concept:
PATHUM WAN
ปทุมวัน

Area
x.xx km²

Population
xx,xxx

Population Density
x,xxx / km²

DEMOGRAPHICS
Population trend / relevant statistics

MOBILITY
Transit station count and map

INFRASTRUCTURE
Healthcare/public facilities

URBAN RISK
Risk indicators / locations
Requirements:
- District-specific map
- Key metrics
- Charts where meaningful
- Facility/station points
- Source and update metadata
- Links to comparison workflow
9.4 Compare — /compare
Allow comparison of approximately 2–4 districts.
Example:
Pathum Wan
     VS
Chatuchak
Compare metrics such as:
- Population
- Area
- Population density
- Transit accessibility
- Healthcare coverage
- Urban risk metric
Use bar charts for metrics where exact comparison matters. A radar chart may be included only when normalized metrics are clearly explained.
Never imply that one district is universally "best" unless the user explicitly defines weights/criteria and the interface explains the scoring formula.
9.5 Data Explorer — /data
Purpose: make the data layer visible and credible.
Example controls:
Dataset: Population
Year: 2026
Metric: Population Density
Display:
Map + Chart + Table
Requirements:
- Dataset selector
- Metric selector
- Year/time selector when available
- Table view
- Visualization
- Source URL/reference
- Last updated/retrieved date
- Basic methodology notes
10. API Design
Suggested endpoints:
GET /api/districts
GET /api/districts/{id}
GET /api/districts/{id}/population
GET /api/districts/{id}/mobility
GET /api/districts/{id}/infrastructure
GET /api/districts/{id}/risk
Analytics:
GET /api/analytics/population-density
GET /api/analytics/transit-accessibility
GET /api/analytics/healthcare-coverage
GET /api/analytics/risk
Comparison:
GET /api/compare?districts=1,5,12
Metadata:
GET /api/datasets
GET /api/datasets/{id}
Use sensible response schemas and validation. GeoJSON endpoints may be introduced where useful.
11. UI/UX Requirements
The application should feel like an urban intelligence/data product, not a generic admin dashboard.
Design goals:
- Map-first interface
- Clean analytical typography
- Strong information hierarchy
- Responsive layout
- Clear map legends
- Useful hover states
- Accessible labels
- Loading/error/empty states
- Consistent metric formatting
- Thai and English district names where available
- Data-source transparency
Avoid excessive animations and decorative components that interfere with analysis.
The map should remain the visual centerpiece.
12. Repository Structure
Use a monorepo structure similar to:
bkk-geospatial-intelligence/
├── frontend/
│   ├── src/
│   └── ...
├── backend/
│   ├── app/
│   ├── tests/
│   └── ...
├── data-pipeline/
│   ├── extract/
│   ├── transform/
│   ├── load/
│   └── pipeline.py
├── database/
│   ├── migrations/
│   ├── schema.sql
│   └── seed/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   └── exploration.ipynb
├── docs/
│   ├── architecture.md
│   ├── data-sources.md
│   ├── database.md
│   └── methodology.md
├── docker-compose.yml
├── .env.example
└── README.md
Notebooks are for exploration only. Production transformation logic must be moved into maintainable Python modules.
Do not commit secrets or credentials.
13. Implementation Roadmap
Week 1 — Data discovery and foundation
Tasks:
- Confirm authoritative district-boundary dataset.
- Find population dataset.
- Document data sources.
- Explore files with GeoPandas.
- Standardize district IDs/names.
Target output:
district
population
area
population_density
geometry
Week 2 — Interactive district map
Tasks:
- Convert/process district geometry for web use.
- Render all 50 districts using MapLibre.
- Implement hover and click interactions.
- Build population-density choropleth.
Target output:
- Working Bangkok map
- 50 selectable districts
- First real analytical layer
Week 3 — Production ETL pipeline
Tasks:
- Separate extract/transform/load logic.
- Add validation.
- Preserve raw data.
- Generate processed district data reproducibly.
Target command:
python pipeline.py
Week 4 — PostgreSQL/PostGIS
Tasks:
- Configure PostgreSQL/PostGIS.
- Create migrations/schema.
- Load district polygons.
- Load population data.
- Implement spatial SQL examples.
Learn/use:
ST_Within
ST_Contains
ST_Intersects
ST_DWithin
ST_Area
ST_Distance
Week 5 — Mobility and infrastructure
Tasks:
- Add transit points.
- Add healthcare/public facility points.
- Spatially assign points to districts.
- Create district-level aggregates.
Target output:
District -> station count
District -> facility count
District -> facilities per population
Week 6 — FastAPI backend
Tasks:
- Build API layer.
- Connect API to PostGIS.
- Add response schemas.
- Add basic tests.
- Add API documentation.
After this stage, frontend production views should retrieve analytical data through FastAPI rather than local CSV files.
Week 7 — Product UI
Build/refine:
- Overview
- District Explorer
- District Profile
- Compare
- Data Explorer
Add responsive behavior, error states, legends, filters, and source metadata.
Week 8 — Production/portfolio polish
Tasks:
- Dockerize services.
- Add Docker Compose.
- Add basic GitHub Actions CI.
- Add tests.
- Optimize large geometry payloads if needed.
- Deploy frontend/backend/database where practical.
- Finish README.
- Add architecture diagram.
- Add screenshots/demo.
- Document methodology and limitations.
14. Future Enhancements
Do not implement these before the MVP is stable.
V2 — Temporal Analysis
Add district + time/year analysis.
Examples:
- Population changes over time
- Infrastructure growth
- Risk changes over time
V3 — District Similarity
Find districts with similar urban profiles.
Potential features:
Population density
Transit accessibility
Infrastructure
Risk indicators
Possible methodology:
1. Select valid metrics.
2. Normalize/standardize them.
3. Calculate similarity or clustering.
4. Explain the methodology in the UI.
Do not present clustering as an objective judgment of district quality.
V4 — Custom District Finder
Allow users to define their own weights.
Example:
Transit          40%
Healthcare       30%
Low Risk         20%
Low Density      10%
Calculate a transparent weighted suitability score.
Requirements:
- User controls the weights.
- Show formula/methodology.
- Show raw metrics alongside scores.
- Do not label the result as universally "best".
15. Testing
Minimum testing targets:
Data pipeline
- Required columns exist.
- District count is expected after boundary processing.
- District IDs/codes are unique.
- Geometry is valid.
- Coordinates fall within sensible ranges.
- Population values are non-negative.
- Spatial joins do not silently drop excessive records.
Backend
- API response schemas
- Invalid district handling
- Database query behavior
- Comparison endpoint validation
Frontend
- Core page rendering
- API loading/error states
- Metric switching
- District selection
- Compare selection constraints
16. Performance Considerations
Geospatial payloads can become large.
Consider:
- Simplifying district geometries for web rendering while preserving analytical originals.
- Serving GeoJSON efficiently.
- Creating PostGIS spatial indexes.
- Creating indexes on district IDs and commonly filtered fields.
- Precomputing expensive district aggregates where justified.
- Avoiding unnecessary repeated spatial joins at request time.
17. Documentation Requirements
README should clearly explain:
1. Problem statement
2. Product screenshots
3. Features
4. Architecture
5. Tech stack
6. Data sources
7. ETL pipeline
8. Database design
9. Spatial-analysis methodology
10. Local setup
11. Docker setup
12. API documentation
13. Testing
14. Limitations
15. Future work
Include an architecture diagram similar to:
Open Data
    |
    v
Python ETL
    |
    v
PostgreSQL + PostGIS
    |
    v
FastAPI
    |
    v
React + MapLibre
18. Portfolio Positioning
The finished project should support this description:
Built an end-to-end geospatial data platform that integrates multiple Bangkok open datasets, processes spatial data through a Python ETL pipeline, stores and analyzes geospatial information using PostgreSQL/PostGIS, exposes district-level analytics through FastAPI, and provides an interactive web application for comparing Bangkok's 50 districts.

Skills demonstrated:
- Python
- SQL
- Pandas
- GeoPandas
- ETL
- Data validation
- PostgreSQL
- PostGIS
- Spatial SQL
- REST API development
- React/TypeScript
- Geospatial visualization
- Docker
- Data analytics
- Data modeling
19. Definition of Done
The MVP is portfolio-ready when all of the following are complete:
- [ ] All 50 Bangkok districts render correctly on an interactive map.
- [ ] Real data is integrated for at least four analytical dimensions.
- [ ] District population density works from source data.
- [ ] Python ETL pipeline is reproducible.
- [ ] Raw and processed data are separated.
- [ ] PostgreSQL/PostGIS stores spatial data.
- [ ] Real spatial queries are used.
- [ ] Point datasets are assigned to districts spatially where appropriate.
- [ ] FastAPI serves frontend analytical data.
- [ ] Overview page works.
- [ ] District Explorer works.
- [ ] District Profile works.
- [ ] District Compare works.
- [ ] Data Explorer works.
- [ ] Sources and update metadata are visible.
- [ ] Loading/error/empty states are handled.
- [ ] Docker configuration works.
- [ ] Basic automated tests exist.
- [ ] README contains architecture, methodology, sources, setup, and screenshots.
- [ ] Application is deployable or has a reproducible local demo.
20. Rules for Astra
When implementing this project:
1. Build the MVP before advanced features.
2. Use real datasets and document every source.
3. Never invent district statistics.
4. Never hardcode analytical rankings.
5. Keep district identifiers standardized across datasets.
6. Use spatial joins instead of manually assigning districts when coordinates are available.
7. Use PostGIS for genuine spatial operations, not merely storage.
8. Keep raw data immutable.
9. Keep notebooks limited to exploration.
10. Move production transformations into Python modules.
11. Frontend analytical data must come from the backend API in the production architecture.
12. Do not introduce machine learning until the core geospatial analytics platform works.
13. Do not over-engineer the stack.
14. Prioritize readable code, clear modules, reproducibility, and documentation.
15. Add comments/documentation around non-obvious geospatial operations and CRS choices.
16. Expose methodology and limitations to users instead of presenting calculated scores as unquestionable facts.
Final Product Vision
BKK Geospatial Intelligence should feel like a small real-world urban intelligence platform rather than a student dashboard.
A user should be able to open Bangkok's map, switch analytical layers, explore any of the 50 districts, understand district-level metrics, compare districts, inspect underlying datasets, and trace analytical results back to documented real-world sources.
The engineering implementation should demonstrate the complete path:
REAL OPEN DATA
      |
      v
DATA ENGINEERING
      |
      v
GEOSPATIAL DATABASE
      |
      v
SPATIAL ANALYTICS
      |
      v
BACKEND API
      |
      v
INTERACTIVE PRODUCT