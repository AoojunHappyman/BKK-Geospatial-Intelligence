from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from urllib.parse import quote
import json
p=Path('.cache/discovery')
urls={
 'arcgis':'https://bmagis.bangkok.go.th/arcgis/rest/services?f=pjson',
 'rail_csv':'https://drt.gdcatalog.go.th/dataset/0462230b-f87e-4335-a870-08b3d7559f9a/resource/1f03a45d-e3b5-4e37-95e6-092dcc75f6ba/download/drt2565_02-1.csv',
 'risk_layer':'https://bmagis.bangkok.go.th/arcgis/rest/services/จุดเสี่ยงน้ำท่วมถนนสายหลัก/FeatureServer/0?f=pjson',
 'health_search':'https://data.bangkok.go.th/api/3/action/package_search?q=health&rows=10',
}
def fetch(item):
 n,u=item
 try:
  b=urlopen(quote(u,safe=':/?=&'),timeout=30).read();(p/(n+'.txt')).write_bytes(b)
  print(n,b.decode('utf-8-sig')[:16000],flush=True)
 except Exception as e:print(n,e,flush=True)
if __name__=='__main__':list(ThreadPoolExecutor(4).map(fetch,urls.items()))
