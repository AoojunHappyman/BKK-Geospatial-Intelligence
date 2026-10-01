from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urlencode
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'data-pipeline'))
from extract.sources import preserve
query='[out:json][timeout:45];nwr["railway"="station"](13.4,100.2,14.1,100.95);out center tags;'
url='https://overpass-api.de/api/interpreter?'+urlencode({'data':query})
with urlopen(Request(url,headers={'User-Agent':'BKKGeospatialIntelligence/1.0'}),timeout=60) as r:raw=r.read()
path,digest=preserve(raw,'json')
doc=json.loads(raw)
hits=[e for e in doc['elements'] if any(k in str(e['tags']) for k in ['PK0','YL0','MT0','สายสีชมพู','สายสีเหลือง'])]
print('snapshot',path,digest,'elements',len(doc['elements']))
print(json.dumps(hits[:12],ensure_ascii=False))
(ROOT/'.cache/osm_snapshot.json').write_text(json.dumps({'path':path,'sha256':digest,'url':url}),encoding='utf-8')
