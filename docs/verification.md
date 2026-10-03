# Verification — 3 October 2026 (Asia/Bangkok)

## Remote CI and fresh Docker verification

[GitHub Actions run 37134751031](https://github.com/AoojunHappyman/BKK-Geospatial-Intelligence/actions/runs/37134751031) passed for commit `d6fa646`. Both independent Ubuntu jobs completed successfully.

- Integration: offline ETL, real PostGIS, 9 backend tests, frontend production build and all 15 Chromium browser tests passed.
- Docker: fresh checkout explicitly checked for absence of `.runtime`, `.local`, `.cache`, `.env` and frontend dependencies. With a CI-only password supplied through the environment, `docker compose up --build -d` built images and started PostGIS → ETL → API → Nginx using a new named database volume, without host application processes or runtime files.
- Public HTTP checks through Nginx on port 8080 confirmed SPA deep links, 50 unique district records, 50 geometries, population 5,422,568, sex-total reconciliation and 51-line CSV export.
- All 9 backend tests passed inside the API container; all 15 browser tests passed against the containerized production frontend and API. Container status/logs are retained in the run’s `docker-verification` artifact. Temporary containers and the CI database volume were removed after verification.
- Fixed two browser-test races found on Linux: wait for the empty CSV export URL to update, and select the expected healthcare POI by its API-provided name. Ranking assertions also wait for the rendered order. No fixed sleeps or automatic test retries were added.
- This validates Linux Docker on GitHub-hosted runners. Docker Desktop on this Windows development host and public hosting remain untested. Earlier local verification notes below describe their original scope.


## Verified locally

- Real PostgreSQL 17.11 with PostGIS 3.6.2, not SQLite standing in for spatial SQL.
- Offline ETL rerun completed successfully from preserved raw snapshots; 50 districts, population 5,422,568, health centers 69, historical flood points 737, transit records 195 (152 assigned, 43 outside Bangkok).
- Python integration/transform suite: 7 passed. One upstream Starlette TestClient deprecation warning; tests remain functional.
- TypeScript and Vite production build succeeded. MapLibre worker is explicitly bundled through Vite's worker pipeline; merely finding a canvas was insufficient and the regression test now verifies 50 rendered district features.
- Browser suite covers all five pages, real polygon click navigation, metric switching, 2–4 district comparison limits, source metadata, 51-line CSV export, API error/retry, loading, empty search and mobile overflow.
- Original five browser scenarios passed against both development and production preview. Added loading and polygon-click checks passed in targeted production tests.
- Desktop overview, comparison and mobile overview screenshots visually inspected after correcting a worker-loading failure.
- Local startup script tested for existing services and for starting API/frontend after stopping previous sessions.
- Docker Compose and GitHub Actions YAML parsed successfully. This is syntax validation only.
- npm audit of production dependencies reports no known vulnerabilities at verification time.

## Not yet verified / next operational steps

### Exploration UX follow-up

Added in-place district details, cross-page comparison tray and shareable URL state. TypeScript/Vite build passed; all 9 browser scenarios passed on the local development server, including the three new end-to-end checks for URL/clipboard/reload/back navigation, invalid/duplicate/over-limit district IDs, and mobile layout/clipboard fallback. Updated desktop/mobile screenshots are in `docs/screenshots/explore-flow*.png`. The mobile layout was refined after visual inspection to reserve scrolling space above the fixed comparison tray. This follow-up does not change ETL, database or API calculations.

- Docker is unavailable on this Windows host; Linux container builds/startup and integration are now verified remotely as recorded above.
- GitHub Actions has now run successfully on the remote repository (see run above).
- No public hosting deployment was requested or performed. The local demo is available with reproducible setup instructions.
- Frontend bundle includes MapLibre and triggers Vite's 500 kB chunk warning; the main asset is approximately 375 kB gzipped, plus a separate worker. Performance budgeting/code splitting is future optimization.
- Source licensing remains unspecified where publishers did not provide verified terms; source data is not relicensed here.
- Single-period MVP: no historical trend analysis, network walking times, ML or composite district score.

## Requirements status

### Page-by-page analytics follow-up

Overview now provides Top/Bottom 5 and a verified six-zone filter. Explorer supports sortable columns (including selected comparison state) and server-generated CSV of the exact filtered rows in display order. Profile provides city benchmark badges, real age-sex population pyramids and POI buttons that move the map/open a popup. Migration 002 and the ETL load 50 zone memberships and 5,100 source age-sex rows, with per-district reconciliation. Existing installations must rerun the ETL and restart the API.

Verification: 15 browser tests and 9 backend tests passed; TypeScript/Vite production build passed. Tests compare pyramid male/female counts with source CSV, validate benchmark formulas and zone coverage, and check sorted filtered/empty CSV output, URL state and POI behavior. Desktop pyramid, mobile pyramid, zone-ranking and POI screenshots were reviewed. A transient old-POI flash while changing API URLs was fixed. Fonts are bundled locally with their SIL OFL licenses; no Google Fonts request is required. Browser-test workers are limited to two for consistent resource use on the development host. Docker/remote CI remain outside this local verification.

### Geospatial UX and readability follow-up

Added a cached OSM Chao Phraya reference line, district labels, cursor-following bounded tooltip with unweighted district mean, stronger choropleth ramp/no-data legend, and Fit Bangkok control. Secondary typography is 11–12 px minimum (the zero-size navigation text rule intentionally hides text in icon-only layouts). Secondary text colors were darkened. Route-shaped loading skeletons replace the page spinner and disable shimmer under reduced-motion settings.

Validation: frontend build passed, 9 existing browser scenarios plus 3 new geospatial/readability/loading scenarios passed; 7 backend tests passed with real PostGIS. New checks verify rendered river/labels, tooltip motion/Escape, camera reset, selected overview text contrast ≥4.5:1, skeleton geometry and reduced motion. Desktop/mobile and skeleton screenshots were visually reviewed. These are targeted accessibility checks, not a full WCAG conformance audit or a measured CLS guarantee.

The MVP's data/ETL/PostGIS/API/five-page frontend, source metadata, real spatial analytics, loading/error/empty handling, automated tests, screenshots and local demo are implemented. Docker runtime verification is now complete on a fresh Linux CI runner, closing the outstanding Docker Definition-of-Done item from `PROJECT_SPEC.md`.

## Linked population-density / rail-proximity chart

The overview includes a scatter plot of registered population density (people/km²) against district land area within an 800 m straight-line radius of rail stations (%). Each point shares district selection with the map/details panel and the existing URL, including reload/back navigation. Six-zone filtering applies to the chart; reference lines use unweighted means of all districts with both measures, so thresholds and axes remain stable between zones. Missing pairs are excluded and reported; zero coverage stays visible.

The highlighted upper-left group is a starting point for further study, not an investment-priority score. Coverage is land area, not population access or walking distance. Users can select overlapping points via the district dropdown, use keyboard selection, and open district profiles. Mobile horizontal scrolling keeps the selected point in view.

Validation: production build and the full 18-test browser suite passed locally. Three new browser scenarios cover API-to-coordinate agreement, candidate membership, map/chart selection, URL/reload/back, zone thresholds, keyboard/mobile layout, and missing/zero/empty data. Desktop/mobile chart screenshots were reviewed. These changes have not yet been run through remote CI.
