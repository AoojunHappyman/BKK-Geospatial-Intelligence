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

