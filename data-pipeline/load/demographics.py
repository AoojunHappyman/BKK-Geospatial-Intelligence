import csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def load_demographics(conn,upsert_source):
    path=ROOT/'data-pipeline/config/district_zones.json'
    config=json.loads(path.read_text(encoding='utf-8'))
    districts=conn.execute('SELECT district_code,name_th FROM district').fetchall()
    names=[name for members in config['zones'].values() for name in members]
    if len(names)!=50 or len(set(names))!=50 or set(names)!={r['name_th'] for r in districts}:
        raise ValueError('Zone mapping must cover all 50 districts exactly once')
    by_name={r['name_th']:r['district_code'] for r in districts}
    upsert_source(conn,dict(source_id='district_zones',name='กลุ่มการปฏิบัติงาน 6 โซน',organization='กรุงเทพมหานคร / สำนักงานปกครองและทะเบียน',url=config['source_url'],retrieved_at=datetime.now(timezone.utc).isoformat(),last_updated=None,reference_period=config['reference'],license=None,raw_format='Verified mapping JSON',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),raw_path=path.relative_to(ROOT).as_posix(),notes='ถอดรายชื่อจากหัวข้อคำสั่ง 2460/2552 ตรวจสอบ '+config['verified_date']+' เป็นกลุ่มการปฏิบัติงาน ไม่ใช่การจัดกลุ่มด้วยโมเดล'),50)
    with conn.cursor() as cursor:
        cursor.executemany('INSERT INTO district_zone VALUES(%s,%s,%s) ON CONFLICT(district_code) DO UPDATE SET zone=excluded.zone,source_id=excluded.source_id',[(by_name[name],zone,'district_zones') for zone,members in config['zones'].items() for name in members])
        with (ROOT/'data/processed/district_population_age_2025.csv').open(encoding='utf-8-sig',newline='') as f:
            records=list(csv.DictReader(f))
        if len(records)!=5100:raise ValueError('Expected 102 age rows × 50 districts')
        cursor.executemany('''INSERT INTO population_age VALUES(%s,%s,%s,%s,%s,%s,%s)
         ON CONFLICT(district_code,reference_period,age_lower) DO UPDATE SET age_upper=excluded.age_upper,male=excluded.male,female=excluded.female,source_id=excluded.source_id''',
         [(r['district_code'],r['reference_period']+'-01',int(r['age_lower']),int(r['age_upper']) if r['age_upper'] else None,int(r['male']),int(r['female']),'population_age') for r in records])
    bad=conn.execute('''SELECT p.district_code FROM population p LEFT JOIN population_age a USING(district_code,reference_period)
     GROUP BY p.district_code,p.reference_period,p.age_classified_total
     HAVING count(a.age_lower)<>102 OR sum(a.male+a.female)<>p.age_classified_total''').fetchall()
    if bad:raise ValueError('Age-sex population reconciliation failed')
