"""Download public source snapshots; never execute downloaded content."""
from pathlib import Path
from urllib.request import urlopen, Request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
SOURCES = {
 'population_district_2568.txt': 'https://stat.bora.dopa.go.th/new_stat/file/68/stat_a68.txt',
 'population_province_2568.txt': 'https://stat.bora.dopa.go.th/new_stat/file/68/stat_c68.txt',
 'population_age_bangkok_2568.txt': 'https://stat.bora.dopa.go.th/new_stat/file/6812/6812cc10.txt',
 'age_dictionary.html': 'https://stat.bora.dopa.go.th/new_stat/webPage/statByAge.php',
 'district_boundaries.zip': 'https://data.bangkok.go.th/dataset/e537025b-1cf6-4c5b-8e46-c2e976f13283/resource/d7be7e84-9d84-4595-bf8f-79b0bc01f1ae/download/district-2.zip',
}
def download(item):
 name,url=item
 path=RAW/name
 try:
  if path.exists():
   previous=json.loads((RAW/'manifest.json').read_text(encoding='utf-8'))
   item=next(r for r in previous if r['url']==url)
   if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
    raise ValueError('Existing raw snapshot checksum mismatch; refusing to overwrite')
   return item
  req=Request(url,headers={'User-Agent':'BKKGeospatialResearch/0.1'})
  with urlopen(req, timeout=45) as response:
   content=response.read()
   final_url=response.url
   content_type=response.headers.get('Content-Type')
  if name.endswith('.zip') and not content.startswith(b'PK'):
   raise ValueError('Expected ZIP, received '+str(content_type))
  path.write_bytes(content)
  return {'file':str(path.relative_to(ROOT)), 'url':url, 'resolved_url':final_url,
   'retrieved_at':datetime.now(timezone.utc).isoformat(), 'bytes':len(content),
   'sha256':hashlib.sha256(content).hexdigest(),'content_type':content_type,'status':'downloaded'}
 except Exception as e:
  return {'file':str(path.relative_to(ROOT)),'url':url,'status':'failed','error':str(e)}
if __name__ == '__main__':
 RAW.mkdir(parents=True,exist_ok=True)
 results=list(ThreadPoolExecutor(5).map(download,SOURCES.items()))
 (RAW/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(results,ensure_ascii=True,indent=2))
