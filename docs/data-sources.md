# Data sources and provenance

URLs, timestamps, byte counts and SHA256 hashes for the exact downloaded files are in `data/raw/manifest.json` and `data/source_catalog.json`. The API and Data Explorer expose the loaded metadata. Raw snapshots are immutable; refresh writes content-addressed files and updates the selected catalog.

| Source | Period / coverage | Entry point |
|---|---|---|
| BMA district boundaries | Resource dated March 2021; 50 districts | [BMA Open Data](https://data.bangkok.go.th/dataset/e537025b-1cf6-4c5b-8e46-c2e976f13283) |
| DOPA district population | December 2025 / BE 2568 | [District text](https://stat.bora.dopa.go.th/new_stat/file/68/stat_a68.txt) |
| DOPA age distribution | December 2025 / Bangkok | [Age text](https://stat.bora.dopa.go.th/new_stat/file/6812/6812cc10.txt) |
| DRT rail stations | Downloaded October 2026; Status=1 records only | [DRT catalog](https://drt.gdcatalog.go.th/dataset/0462230b-f87e-4335-a870-08b3d7559f9a) |
| OpenStreetMap station nodes | Snapshot supplement for missing coordinates | [Overpass API](https://overpass-api.de/) |
| BMA public health centers | 69 records; survey year unspecified | [FeatureServer](https://bmagis.bangkok.go.th/arcgis/rest/services/riskbkk/RISK_ADMIN_Health_Center/FeatureServer/0) |
| BMA flood lessons | 2022 / BE 2565; 737 points | [FeatureServer](https://bmagis.bangkok.go.th/arcgis/rest/services/ปัญหาน้าท่วมจากการถอดบทเรียน_2565/FeatureServer/0) |

The rail catalog metadata date is separate from snapshot retrieval and the observation date. It is not proof of current operational completeness. BMA health center links in its open-data portal failed during import; the public BMA GIS service above was used and documented instead.

OSM data is © OpenStreetMap contributors, available under [ODbL 1.0](https://www.openstreetmap.org/copyright). Source-specific license fields that could not be verified are explicitly null; public access alone is not a license grant. This repository does not relicense source datasets. Check publisher terms before redistributing snapshots or publishing a derived database. Code licensing has not been selected by the project owner.

ArcGIS extraction fetches object IDs then paginates records, checking total counts to avoid service transfer limits. Downloads fail on missing schemas, duplicated IDs or unacceptable coordinate rejection rates. The ETL reports skipped DRT records (Status other than 1) explicitly; they are not fabricated as active stations.
