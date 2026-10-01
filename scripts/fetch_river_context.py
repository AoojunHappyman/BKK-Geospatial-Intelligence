"""Cache a real OSM river centerline for offline map context; never used in metrics."""
import hashlib,json,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
query='[out:json][timeout:60];way["waterway"="river"]["name"~"เจ้าพระยา|Chao Phraya",i](13.4,100.2,14.1,101.0);out geom;'
for endpoint in ['https://overpass.kumi.systems/api/interpreter','https://overpass-api.de/api/interpreter']:
    url=endpoint+'?'+urllib.parse.urlencode({'data':query})
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'BKK-Geospatial-Intelligence/1.0'})
        raw=urllib.request.urlopen(request,timeout=50).read()
        break
    except Exception:
        if endpoint.endswith('overpass-api.de/api/interpreter'):raise
payload=json.loads(raw)
features=[]
for way in payload.get('elements',[]):
    coordinates=[[p['lon'],p['lat']] for p in way.get('geometry',[])]
    if len(coordinates)>1:
        features.append(dict(type='Feature',id=way['id'],properties={'name':'แม่น้ำเจ้าพระยา','osm_way_id':way['id']},geometry={'type':'LineString','coordinates':coordinates}))
if not features:raise ValueError('No river geometries returned')
digest=hashlib.sha256(raw).hexdigest()
snapshot=ROOT/'data/raw/snapshots'/f'{digest}.json'
if not snapshot.exists():snapshot.write_bytes(raw)
dest=ROOT/'frontend/public/context';dest.mkdir(parents=True,exist_ok=True)
(dest/'chao-phraya.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False),encoding='utf-8')
(dest/'source.json').write_text(json.dumps(dict(name='Chao Phraya river centerline',url=url,retrieved_at=datetime.now(timezone.utc).isoformat(),sha256=digest,raw_path=snapshot.relative_to(ROOT).as_posix(),license='ODbL 1.0',attribution='© OpenStreetMap contributors',notes='River centerline for orientation only; not riverbank geometry or an analytical input.',features=len(features)),ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Saved {len(features)} OSM river segments; SHA256 {digest}')
