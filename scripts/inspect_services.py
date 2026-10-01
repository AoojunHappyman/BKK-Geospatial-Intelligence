"""Read public service metadata for source discovery."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen
import json, re

URLS = {
 'facilities': 'https://gistdaportal.gistda.or.th/data/rest/services/fac_bkk/MapServer?f=pjson',
 'risk_map': 'https://bmagis.bangkok.go.th/portal/sharing/rest/content/items/a42d60e681724e11942980cd78dfb52a/data?f=json',
 'bma_services': 'https://bmagis.bangkok.go.th/server/rest/services?f=pjson',
 'postgis': 'https://download.osgeo.org/postgis/windows/pg17/',
 'postgres': 'https://www.enterprisedb.com/download-postgresql-binaries',
 'rail': 'https://data.go.th/th/dataset/rail_station',
}
def get(item):
 name,url=item
 try:
  raw=urlopen(url,timeout=35).read()
  p=Path('.cache/discovery');p.mkdir(parents=True,exist_ok=True)
  (p/(name+'.txt')).write_bytes(raw)
  text=raw.decode('utf-8')
  if name in ('postgis','postgres'):
   text='\n'.join(re.findall(r'''(?:href|src)=["']([^"']+)["']''',text))
  elif name=='rail':
   text='\n'.join(line for line in text.splitlines() if 'metadata:' in line)
  return name,text[:26000]
 except Exception as exc:return name,str(exc)
if __name__=='__main__':
 for name,text in ThreadPoolExecutor(6).map(get,URLS.items()):print(name, text, flush=True)
