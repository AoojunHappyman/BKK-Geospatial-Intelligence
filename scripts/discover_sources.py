from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import re, json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'raw' / 'discovery'
OUT.mkdir(parents=True, exist_ok=True)
URLS = {
 'age_2025': 'https://stat.bora.dopa.go.th/new_stat/webPage/statByProvince.php?year=68',
 'population': 'https://stat.bora.dopa.go.th/new_stat/webPage/statByYear.php',
 'boundary': 'https://data.go.th/en/dataset/50',
 'bma_population': 'https://economy.bangkok.go.th/html_statistic/index2.php?group_id=581',
}
def fetch(item):
 name,url=item
 try:
  content=urlopen(url,timeout=35).read()
  (OUT/(name+'.html')).write_bytes(content)
  try: html=content.decode('utf-8')
  except UnicodeDecodeError: html=content.decode('cp874')
  links=re.findall(r'''(?:href|src)\s*=\s*["']([^"']+)["']''',html)
  return {'name':name,'url':url,'links':links}
 except Exception as e: return {'name':name,'error':str(e)}
if __name__ == '__main__':
 for result in ThreadPoolExecutor(4).map(fetch, URLS.items()):
  print(json.dumps(result,ensure_ascii=True))
