"""Verify a running deployment through its public HTTP entry point (stdlib only)."""
import argparse
import json
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8080')
args = parser.parse_args()
base = args.url.rstrip('/')

def get(path):
    with urllib.request.urlopen(base + path, timeout=10) as response:
        return response.read().decode('utf-8-sig')

deadline = time.monotonic() + 120
while True:
    try:
        health = json.loads(get('/api/health'))
        break
    except (urllib.error.URLError, TimeoutError):
        if time.monotonic() >= deadline:
            raise
        time.sleep(2)

assert health['districts'] == 50, health
assert '<html' in get('/').lower()
assert '<html' in get('/district/1007').lower(), 'SPA deep link failed'
rows = json.loads(get('/api/districts'))
assert len(rows) == len({r['district_code'] for r in rows}) == 50
assert sum(r['population_total'] for r in rows) == 5422568
assert all(r['male_population'] + r['female_population'] == r['population_total'] for r in rows)
geometry = json.loads(get('/api/districts/geojson'))
assert len(geometry['features']) == 50
assert len(get('/api/export/districts.csv').strip().splitlines()) == 51
print('Deployment verified: HTTP/SPA, PostGIS, 50 unique districts/geometries, population 5,422,568 and CSV.')
