import csv
import io
import logging
from typing import Literal
import psycopg
from psycopg import sql
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from .db import connection
from .metrics import METRICS, METRIC_IDS
from .schemas import District, FeatureCollection

app = FastAPI(title='BKK Geospatial Intelligence', version='1.0.0',
    description='District analytics from documented Bangkok public data. Identifiers are district codes 1001–1050.')
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.exception_handler(psycopg.OperationalError)
def database_unavailable(request, exc):
    logging.getLogger(__name__).error('Database unavailable: %s', type(exc).__name__)
    return JSONResponse(status_code=503, content={'detail':'Database unavailable. Check service health.'})

def district_rows(codes=None):
    with connection() as conn:
        query='SELECT * FROM district_metrics'
        params=()
        if codes is not None:
            query+=' WHERE district_code = ANY(%s)'; params=(codes,)
        return conn.execute(query+' ORDER BY district_code',params).fetchall()

def find_district(code):
    rows=district_rows([code])
    if not rows: raise HTTPException(404,'District not found')
    return rows[0]

@app.get('/api/health')
def health():
    with connection() as conn:
        info=conn.execute('SELECT postgis_version() AS postgis, (SELECT count(*) FROM district) AS districts').fetchone()
    return {'status':'ok',**info}

@app.get('/api/metrics')
def metrics(): return METRICS

@app.get('/api/districts',response_model=list[District])
def districts(): return district_rows()

@app.get('/api/districts/geojson',response_model=FeatureCollection)
def geometry():
    with connection() as conn:
        rows=conn.execute('''SELECT district_code,name_th,name_en,
            ST_AsGeoJSON(ST_Transform(ST_SimplifyPreserveTopology(ST_Transform(geometry,32647),15),4326),6)::json AS geometry
            FROM district ORDER BY district_code''').fetchall()
    return {'type':'FeatureCollection','features':[dict(type='Feature',id=r['district_code'],
        properties={k:r[k] for k in ('district_code','name_th','name_en')},geometry=r['geometry']) for r in rows]}

@app.get('/api/districts/{code}',response_model=District)
def district(code:str): return find_district(code)

@app.get('/api/districts/{code}/population')
def population(code:str):
    row=find_district(code)
    return {k:row[k] for k in ('district_code','reference_period','population_total','male_population','female_population','age_0_14','age_15_59','age_60_plus','age_classified_total','outside_age_series','older_share')}

def points(kind, code=None):
    with connection() as conn:
        rows=conn.execute('''SELECT source_record_id,name,category,district_code,assignment_status,
            ST_AsGeoJSON(geometry)::json AS geometry FROM point_location
            WHERE kind=%s AND (%s::text IS NULL OR district_code=%s) ORDER BY source_record_id''',(kind,code,code)).fetchall()
    return dict(type='FeatureCollection', features=[dict(type='Feature',id=r['source_record_id'],
        geometry=r['geometry'],properties={k:v for k,v in r.items() if k!='geometry'}) for r in rows])

@app.get('/api/points/{kind}',response_model=FeatureCollection)
def point_layer(kind:Literal['transit','healthcare','risk']):return points(kind)

@app.get('/api/districts/{code}/mobility',response_model=FeatureCollection)
def mobility(code:str):find_district(code);return points('transit',code)

@app.get('/api/districts/{code}/infrastructure',response_model=FeatureCollection)
def infrastructure(code:str):find_district(code);return points('healthcare',code)

@app.get('/api/districts/{code}/risk',response_model=FeatureCollection)
def risk(code:str):find_district(code);return points('risk',code)

@app.get('/api/analytics/{metric}')
def analytics(metric:str):
    aliases={'population-density':'population_density','transit-accessibility':'transit_coverage',
             'healthcare-coverage':'healthcare_per_100k','risk':'risk_location_count'}
    metric=aliases.get(metric,metric)
    if metric not in METRIC_IDS:raise HTTPException(404,'Unknown metric')
    with connection() as conn:
        rows=conn.execute(sql.SQL('''SELECT district_code,name_th,{metric} AS value,
          CASE WHEN {metric} IS NOT NULL THEN dense_rank() OVER(ORDER BY {metric} DESC NULLS LAST) END AS rank
          FROM district_metrics ORDER BY {metric} DESC NULLS LAST,district_code''').format(metric=sql.Identifier(metric))).fetchall()
    return {'metric':next(m for m in METRICS if m['id']==metric),'districts':rows}

@app.get('/api/compare',response_model=list[District])
def compare(districts:str=Query(...)):
    codes=[s.strip() for s in districts.split(',')]
    if not 2<=len(codes)<=4 or len(set(codes))!=len(codes):
        raise HTTPException(422,'Select 2–4 distinct district codes')
    rows=district_rows(codes)
    if len(rows)!=len(codes):raise HTTPException(404,'One or more districts not found')
    by_code={r['district_code']:r for r in rows}
    return [by_code[c] for c in codes]

@app.get('/api/datasets')
def datasets():
    with connection() as conn:return conn.execute('SELECT * FROM data_source ORDER BY source_id').fetchall()

@app.get('/api/datasets/{source_id}')
def dataset(source_id:str):
    with connection() as conn:r=conn.execute('SELECT * FROM data_source WHERE source_id=%s',(source_id,)).fetchone()
    if not r:raise HTTPException(404,'Dataset not found')
    return r

@app.get('/api/nearby')
def nearby(lon:float=Query(ge=100,le=102),lat:float=Query(ge=13,le=15),
           radius_m:int=Query(default=1000,ge=1,le=10000),kind:Literal['transit','healthcare','risk']='healthcare'):
    with connection() as conn:
        return conn.execute('''SELECT name,category,district_code,
         ST_Distance(geometry::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography) AS distance_m
         FROM point_location WHERE kind=%s AND ST_DWithin(geometry::geography,
         ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s) ORDER BY distance_m LIMIT 100''',
         (lon,lat,kind,lon,lat,radius_m)).fetchall()

@app.get('/api/export/districts.csv')
def export():
    rows=district_rows();buffer=io.StringIO();w=csv.DictWriter(buffer,fieldnames=list(rows[0]))
    w.writeheader();w.writerows(rows)
    return Response('\ufeff'+buffer.getvalue(),media_type='text/csv; charset=utf-8',
        headers={'Content-Disposition':'attachment; filename=bkk-district-metrics.csv'})
