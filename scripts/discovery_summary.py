from pathlib import Path
import re,json
p=Path('.cache/discovery')
print('POSTGIS',re.findall(r'href="([^"]+)"',(p/'postgis.txt').read_text())[-30:])
t=(p/'postgres.txt').read_text();i=t.find('17.11');print('PG',t[i:i+2300])
print('BMA',(p/'bma_services.txt').read_text()[:1000])
print('MAP',json.loads((p/'risk_map.txt').read_text())['map'])
