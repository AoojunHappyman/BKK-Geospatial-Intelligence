from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from urllib.parse import quote
import json
urls=[
 'https://bmagis.bangkok.go.th/arcgis/rest/services/ckan?f=json',
 'https://bmagis.bangkok.go.th/arcgis/rest/services/BMA?f=json',
 'https://bmagis.bangkok.go.th/arcgis/rest/services/riskbkk?f=json',
 'https://bmagis.bangkok.go.th/arcgis/rest/services/RISK_ADMIN_Health_Center/MapServer?f=json',
 'https://data.bangkok.go.th/api/3/action/package_search?q=โรงพยาบาล&rows=20'
]
def get(u):
 try:
  j=json.load(urlopen(quote(u,safe=':/?=&'),timeout=12))
  if 'result' in j:
   out=[(r['title'],[(x['format'],x['url']) for x in r['resources']]) for r in j['result']['results']]
  else:out={k:j.get(k) for k in ['services','layers','error']}
  print(u,json.dumps(out,ensure_ascii=False),flush=True)
 except Exception as e:print(u,str(e),flush=True)
if __name__=='__main__':list(ThreadPoolExecutor(5).map(get,urls))
