"""Download official portable database archives into project-local cache."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def download(item):
 name,url=item
 p=ROOT/'.cache'/name;p.parent.mkdir(exist_ok=True)
 if not p.exists():
  with urlopen(url,timeout=60) as r, p.with_suffix('.partial').open('wb') as f:
   print(name,'downloading',r.headers.get('Content-Length'),flush=True)
   while chunk:=r.read(1024*1024):f.write(chunk)
  p.with_suffix('.partial').replace(p)
 print(name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':
 list(ThreadPoolExecutor(2).map(download,{
  'postgres.zip':'https://sbp.enterprisedb.com/getfile.jsp?fileid=1260616',
  'postgis.zip':'https://download.osgeo.org/postgis/windows/pg17/postgis-bundle-pg17-3.6.2x64.zip'
 }.items()))
