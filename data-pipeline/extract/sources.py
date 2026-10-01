"""Immutable, content-addressed raw snapshots. Offline replay is the default."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.parse import urlencode,quote
ROOT=Path(__file__).resolve().parents[2]

def fetch(url):
    request=Request(quote(url,safe=':/?=&,%'),headers={'User-Agent':'BKKGeospatialIntelligence/1.0'})
    with urlopen(request,timeout=60) as response: return response.read()

def preserve(raw, suffix):
    digest=hashlib.sha256(raw).hexdigest()
    path=ROOT/'data/raw/snapshots'/f'{digest}.{suffix}'
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('Snapshot hash collision')
    else:path.write_bytes(raw)
    return str(path.relative_to(ROOT)).replace('\\','/'),digest

def read_snapshot(path,digest):
    raw=(ROOT/path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError(f'Checksum failed: {path}')
    return raw

def refresh_sources():
    config=json.loads((ROOT/'data-pipeline/config/sources.json').read_text(encoding='utf-8'))
    catalog={}
    for source_id,info in config.items():
        parts=[]
        if info['type'] in ('csv','json'):
            path,digest=preserve(fetch(info['url']),info['type']);parts.append(dict(path=path,sha256=digest))
        else:
            ids=json.loads(fetch(info['url']+'/query?'+urlencode({'where':'1=1','returnIdsOnly':'true','f':'json'})))
            if 'error' in ids:raise ValueError(ids['error'])
            object_ids=sorted(ids['objectIds'])
            if not object_ids:raise ValueError(f'No records for {source_id}')
            for start in range(0,len(object_ids),200):
                query=urlencode({'objectIds':','.join(map(str,object_ids[start:start+200])),
                    'outFields':info['fields'],'outSR':4326,'returnGeometry':'true','f':'json'})
                raw=fetch(info['url']+'/query?'+query)
                doc=json.loads(raw)
                if 'error' in doc or doc.get('exceededTransferLimit'):raise ValueError(f'Incomplete ArcGIS response {source_id}')
                if len(doc['features'])!=len(object_ids[start:start+200]):raise ValueError('ArcGIS count mismatch')
                path,digest=preserve(raw,'json');parts.append(dict(path=path,sha256=digest))
        package=json.dumps(parts,sort_keys=True).encode()
        path,digest=preserve(package,'json')
        catalog[source_id]={**info,'source_id':source_id,'retrieved_at':datetime.now(timezone.utc).isoformat(),
            'raw_path':path,'sha256':digest,'parts':parts}
        print('Extracted',source_id,len(parts),'file(s)',flush=True)
    (ROOT/'data/source_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    return catalog

def load_sources():
    catalog=json.loads((ROOT/'data/source_catalog.json').read_text(encoding='utf-8'))
    for info in catalog.values():
        parts=json.loads(read_snapshot(info['raw_path'],info['sha256']))
        if parts!=info['parts']:raise ValueError('Snapshot manifest mismatch')
        for part in parts:read_snapshot(part['path'],part['sha256'])
    return catalog
