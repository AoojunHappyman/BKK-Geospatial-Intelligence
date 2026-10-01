from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
import json
urls={
 'health_service':'https://bmagis.bangkok.go.th/arcgis/rest/services/RISK_ADMIN_Health_Center/FeatureServer',
 'risk_points':'https://bmagis.bangkok.go.th/arcgis/rest/services/จุดเสี่ยงน้ำท่วมถนนสายรอง_ซอย/FeatureServer/0',
 'risk_2022':'https://bmagis.bangkok.go.th/arcgis/rest/services/ปัญหาน้าท่วมจากการถอดบทเรียน_2565/FeatureServer/0',
 'rail_dictionary':'https://drt.gdcatalog.go.th/dataset/0462230b-f87e-4335-a870-08b3d7559f9a/resource/cd369e2d-19eb-46c2-8ef2-949016dda6df/download/datadic_drt2565_02.csv',
}
def fetch(item):
 n,u=item
 try:
  raw=urlopen(quote(u+('' if n=='rail_dictionary' else '?f=pjson'),safe=':/?=&'),timeout=30).read()
  (Path('.cache/discovery')/(n+'.txt')).write_bytes(raw)
  if n=='rail_dictionary':print(n,raw.decode('utf-8-sig'),flush=True);return
  j=json.loads(raw)
  print(n,json.dumps({k:j.get(k) for k in ['name','layers','geometryType','fields','editingInfo','description','serviceItemId']},ensure_ascii=False),flush=True)
 except Exception as e:print(n,e)
if __name__=='__main__':list(ThreadPoolExecutor(4).map(fetch,urls.items()))
