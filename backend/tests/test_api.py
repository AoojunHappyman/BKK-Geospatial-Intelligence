"""Integration tests against a real, ETL-populated PostGIS database."""
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import connection

pytestmark=pytest.mark.skipif(not os.getenv('DATABASE_URL'),reason='Requires PostGIS integration database')
client=TestClient(app)

def test_health_and_complete_population():
    assert client.get('/api/health').json()['districts']==50
    response=client.get('/api/districts');assert response.status_code==200
    rows=response.json()
    assert len(rows)==50 and len({r['district_code'] for r in rows})==50
    assert sum(r['population_total'] for r in rows)==5422568
    assert all(r['male_population']+r['female_population']==r['population_total'] for r in rows)
    assert all(0<=r['transit_coverage']<=100 for r in rows)

def test_invalid_codes_and_comparison_constraints():
    assert client.get('/api/districts/9999').status_code==404
    for query in ['1001','1001,1001','1001,1002,1003,1004,1005']:
        assert client.get('/api/compare',params={'districts':query}).status_code==422
    assert client.get('/api/compare',params={'districts':'1001,9999'}).status_code==404
    result=client.get('/api/compare',params={'districts':'1030,1007'}).json()
    assert [r['district_code'] for r in result]==['1030','1007']

def test_geometry_sources_and_rankings():
    geo=client.get('/api/districts/geojson').json()
    assert geo['type']=='FeatureCollection' and len(geo['features'])==50
    assert all(f['geometry']['type'] in ('Polygon','MultiPolygon') for f in geo['features'])
    assert all(f['properties']['label_point']['type']=='Point' for f in geo['features'])
    assert all(len(f['properties']['label_point']['coordinates'])==2 for f in geo['features'])
    ranks=client.get('/api/analytics/population-density').json()['districts']
    assert [r['value'] for r in ranks]==sorted([r['value'] for r in ranks],reverse=True)
    assert client.get('/api/analytics/not-a-metric').status_code==404
    assert client.get('/api/datasets/unknown').status_code==404
    for d in client.get('/api/datasets').json():
        assert d['url'].startswith('https://') and len(d['sha256'])==64

def test_points_counted_once_and_radius():
    with connection() as conn:
        assert conn.execute("SELECT count(*) AS n FROM point_location WHERE kind='risk' AND district_code IS NOT NULL").fetchone()['n']==737
        assert conn.execute('SELECT sum(healthcare_facility_count) AS n FROM district_metrics').fetchone()['n']==69
        assert conn.execute('SELECT count(*) AS n FROM district WHERE NOT ST_IsValid(geometry)').fetchone()['n']==0
    nearby=client.get('/api/nearby',params={'lon':100.53,'lat':13.75,'radius_m':3000}).json()
    assert all(0<=r['distance_m']<=3000 for r in nearby)
    assert client.get('/api/nearby',params={'lon':999,'lat':13.7}).status_code==422
    assert client.get('/api/points/invalid').status_code==422

def test_boundary_policy_with_spatial_sql():
    with connection() as conn:
        r=conn.execute("""WITH s AS(SELECT ST_GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))',4326) g,
            ST_SetSRID(ST_MakePoint(0,0.5),4326) p)
            SELECT ST_Within(p,g) AS within,ST_Covers(g,p) AS covers FROM s""").fetchone()
    assert r=={'within':False,'covers':True}

def test_zones_pyramid_and_city_benchmark():
    from collections import Counter
    rows=client.get('/api/districts').json()
    assert sorted(Counter(r['zone'] for r in rows).values())==[7,7,8,9,9,10]
    profile=next(r for r in rows if r['district_code']=='1007')
    assert profile['zone']=='กรุงเทพใต้'
    pyramid=client.get('/api/districts/1007/population-pyramid').json()
    assert len(pyramid['bands'])==21
    assert pyramid['bands'][0]['label']=='100+'
    assert sum(b['male']+b['female'] for b in pyramid['bands'])==profile['age_classified_total']
    assert pyramid['classified_total']+pyramid['excluded_total']==profile['population_total']
    import csv
    from pathlib import Path
    with (Path(__file__).resolve().parents[2]/'data/processed/district_population_age_2025.csv').open(encoding='utf-8-sig') as f:
        source=[r for r in csv.DictReader(f) if r['district_code']=='1007']
    for start in (0,100):
        group=[r for r in source if (int(r['age_lower'])>=100 if start==100 else int(r['age_lower'])<5)]
        actual=next(b for b in pyramid['bands'] if b['age_start']==start)
        assert actual['male']==sum(int(r['male']) for r in group)
        assert actual['female']==sum(int(r['female']) for r in group)
    benchmarks=client.get('/api/benchmarks').json()
    expected=sum(r['population_total'] for r in rows)/sum(r['area_km2'] for r in rows)
    assert benchmarks['population_density']['value']==pytest.approx(expected)
    assert benchmarks['older_share']['value']==pytest.approx(100*sum(r['age_60_plus'] for r in rows)/sum(r['age_classified_total'] for r in rows))
    assert client.get('/api/districts/9999/population-pyramid').status_code==404

def test_filtered_export_preserves_order_and_validates_selection():
    import csv,io
    result=client.get('/api/export/districts.csv?districts=1030,1007')
    rows=list(csv.DictReader(io.StringIO(result.text.lstrip('\ufeff'))))
    assert [r['district_code'] for r in rows]==['1030','1007']
    assert client.get('/api/export/districts.csv?districts=9999').status_code==422
    assert client.get('/api/export/districts.csv?districts=1007,1007').status_code==422
    assert len(client.get('/api/export/districts.csv?districts=').text.splitlines())==1

