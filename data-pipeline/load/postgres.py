import json,os
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb
from psycopg.rows import dict_row
from load.demographics import load_demographics
ROOT=Path(__file__).resolve().parents[2]

def upsert_source(conn,info,count):
    fields=['source_id','name','organization','url','retrieved_at','last_updated','reference_period','license','raw_format','sha256','raw_path','notes']
    conn.execute('''INSERT INTO data_source VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
       ON CONFLICT(source_id) DO UPDATE SET name=excluded.name,organization=excluded.organization,
       url=excluded.url,retrieved_at=excluded.retrieved_at,last_updated=excluded.last_updated,
       reference_period=excluded.reference_period,license=excluded.license,raw_format=excluded.raw_format,
       sha256=excluded.sha256,raw_path=excluded.raw_path,notes=excluded.notes,row_count=excluded.row_count''',
       tuple(info.get(f) for f in fields)+(count,))

def load_all(frame,catalog,points,reports):
    manifest=json.loads((ROOT/'data/raw/manifest.json').read_text(encoding='utf-8'))
    def original(filename,source_id,name,org,period,notes):
        item=next(r for r in manifest if Path(r['file']).name==filename or r['file'].replace('\\','/').endswith('/'+filename))
        return dict(source_id=source_id,name=name,organization=org,url=item['url'],retrieved_at=item['retrieved_at'],
            last_updated='2021-03-09' if source_id=='districts' else None,reference_period=period,license=None,
            raw_format='Shapefile ZIP' if source_id=='districts' else 'pipe-delimited text',
            sha256=item['sha256'],raw_path=item['file'].replace('\\','/'),notes=notes)
    with psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row) as conn:
        conn.execute((ROOT/'database/migrations/001_initial.sql').read_text(encoding='utf-8'))
        conn.execute((ROOT/'database/migrations/002_demographics_zones.sql').read_text(encoding='utf-8'))
        upsert_source(conn,original('district_boundaries.zip','districts','ขอบเขต 50 เขต','กรุงเทพมหานคร','ทรัพยากร 2021-03-09','พื้นที่คำนวณจาก polygon ไม่ใช่พื้นที่สถิติทางการ วันที่ขอบเขตมีผลไม่ระบุ'),50)
        upsert_source(conn,original('population_district_2568.txt','population','ประชากรและอายุรายเขต','กรมการปกครอง','2025-12','อายุครอบคลุมประชากรไทยในชุดแจกแจงอายุ รายละเอียด source ทั้งหมดใน data/raw/manifest.json'),50)
        upsert_source(conn,original('population_age_bangkok_2568.txt','population_age','ประชากรแยกอายุรายเขต','กรมการปกครอง','2025-12','เฉพาะผู้มีสัญชาติไทยในชุดแจกแจงอายุ เก็บหมวดนอกชุดอายุแยกไว้'),5100)
        if 'osm_transit' in catalog:
            upsert_source(conn,catalog['osm_transit'],reports['transit']['osm_coordinates'])
        for _,r in frame.iterrows():
            conn.execute('''INSERT INTO district VALUES(%s,%s,%s,ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)),%s)
             ON CONFLICT(district_code) DO UPDATE SET name_th=excluded.name_th,name_en=excluded.name_en,geometry=excluded.geometry,source_id=excluded.source_id''',
             (r.district_code,r.district_name_th,r.district_name_en,json.dumps(r.geometry.__geo_interface__),'districts'))
            vals=[int(r[k]) for k in ['population_total','population_male','population_female','population_age_0_14','population_age_15_59','population_age_60_plus','age_classified_thai_population','population_outside_age_series']]
            conn.execute('''INSERT INTO population VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
             ON CONFLICT(district_code,reference_period) DO UPDATE SET population_total=excluded.population_total,
             male_population=excluded.male_population,female_population=excluded.female_population,
             age_0_14=excluded.age_0_14,age_15_59=excluded.age_15_59,age_60_plus=excluded.age_60_plus,
             age_classified_total=excluded.age_classified_total,outside_age_series=excluded.outside_age_series,source_id=excluded.source_id''',
             (r.district_code,r.reference_period+'-01',*vals,'population'))
        load_demographics(conn,upsert_source)
        for source_id,records in points.items():
            upsert_source(conn,catalog[source_id],len(records))
            conn.execute('DELETE FROM point_location WHERE source_id=%s',(source_id,))
            with conn.cursor() as cursor:
                cursor.executemany('''INSERT INTO point_location(source_id,source_record_id,kind,name,category,geometry,properties)
                 VALUES(%s,%s,%s,%s,%s,ST_SetSRID(ST_MakePoint(%s,%s),4326),%s)''',
                 [(source_id,r['id'],source_id,r['name'],r['category'],r['lon'],r['lat'],Jsonb(r['properties'])) for r in records])
        # ST_Covers includes boundary points; multiple matches are not silently counted twice.
        conn.execute('''WITH matches AS (
            SELECT p.source_id,p.source_record_id,count(d.district_code) AS n,min(d.district_code) AS code
            FROM point_location p LEFT JOIN district d ON ST_Covers(d.geometry,p.geometry)
            GROUP BY p.source_id,p.source_record_id)
            UPDATE point_location p SET district_code=CASE WHEN m.n=1 THEN m.code END,
            assignment_status=CASE WHEN m.n=1 THEN 'assigned' WHEN m.n=0 THEN 'outside' ELSE 'ambiguous_boundary' END
            FROM matches m WHERE p.source_id=m.source_id AND p.source_record_id=m.source_record_id''')
        assignment=conn.execute('SELECT kind,assignment_status,count(*) AS count FROM point_location GROUP BY 1,2 ORDER BY 1,2').fetchall()
        for kind in ('healthcare','risk'):
            missing=sum(r['count'] for r in assignment if r['kind']==kind and r['assignment_status']!='assigned')
            if missing/max(len(points[kind]),1)>.05:raise ValueError(f'Excessive unassigned {kind}: {missing}')
        conn.execute((ROOT/'database/aggregate.sql').read_text(encoding='utf-8'))
        summary=conn.execute('SELECT count(*) AS districts,sum(population_total) AS population FROM district_metrics').fetchone()
        if summary['districts']!=50:raise ValueError('District metrics incomplete')
        report=dict(transforms=reports,spatial_assignments=assignment,summary=summary)
        conn.execute('INSERT INTO etl_run(report) VALUES(%s)',(Jsonb(report),))
    (ROOT/'data/processed/etl_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

