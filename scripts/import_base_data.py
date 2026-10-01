"""Build a validated Bangkok district dataset from pinned official snapshots.

Run after download_base_data.py. No network access is used here.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import sqlite3
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.runtime'))
import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform, unary_union
from shapely import make_valid

RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'processed'
PERIOD = '2025-12'
SOURCE_PERIOD = '6812'
BOUNDARY_RESOURCE_DATE = '2021-03-09'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_pipe(name, width):
    rows = []
    for line in (RAW / name).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        fields = [x.strip() for x in line.split('|')]
        if fields[-1] == '':
            fields.pop()
        require(len(fields) == width, f'{name}: expected {width} fields, got {len(fields)}')
        rows.append(fields)
    return rows


def number(value):
    result = int(value.replace(',', ''))
    require(result >= 0, 'Negative population')
    return result


def write_csv(name, rows):
    require(bool(rows), f'Empty output {name}')
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_population():
    rows = read_pipe('population_district_2568.txt', 13)
    bkk = [r for r in rows if r[1] == '10']
    require(all(r[0] == SOURCE_PERIOD for r in bkk), 'Population period mismatch')
    districts = {}
    for row in bkk:
        if row[3] == '0':
            continue
        code = row[3]
        require(code not in districts, f'Duplicate population code {code}')
        require(row[4].startswith('ท้องถิ่นเขต'), f'Unexpected registry name {row[4]}')
        male, female, total, houses = map(number, row[9:13])
        require(male + female == total, f'Sex total mismatch {code}')
        districts[code] = dict(district_code=code,
            district_name_th=row[4].removeprefix('ท้องถิ่นเขต'),
            reference_period=PERIOD, population_male=male,
            population_female=female, population_total=total, registered_houses=houses)
    require(set(districts) == {str(x) for x in range(1001, 1051)}, 'Expected district codes 1001–1050')
    controls = [r for r in read_pipe('population_province_2568.txt', 13) if r[1] == '10']
    require(len(controls) == 1 and controls[0][0] == SOURCE_PERIOD, 'Invalid Bangkok control row')
    control = dict(zip(('population_male', 'population_female', 'population_total', 'registered_houses'),
                       map(number, controls[0][9:13])))
    for field, expected in control.items():
        require(sum(r[field] for r in districts.values()) == expected, f'Bangkok sum mismatch {field}')
    return districts, control


def load_ages(population):
    rows = read_pipe('population_age_bangkok_2568.txt', 220)
    names = {r['district_name_th']: code for code, r in population.items()}
    require(len(names) == 50, 'Population names are not unique')
    district_rows = [r for r in rows if r[0].startswith('เขต')]
    require(len(district_rows) == 50, 'Expected 50 district age rows')
    province_rows = [r for r in rows if r[0] == 'กรุงเทพมหานคร']
    require(len(province_rows) == 1, 'Expected one Bangkok age control')
    province_values = list(map(number, province_rows[0][1:]))
    values_by_code, age_records, extras, summary, crosswalk = {}, [], [], {}, []
    categories = ('lunar_birth_year', 'central_house_register', 'non_thai_nationality', 'in_migration')
    for row in district_rows:
        name = row[0].removeprefix('เขต')
        require(name in names, f'Unmatched district age name {name}')
        code = names[name]
        require(code not in values_by_code, f'Duplicate age district {code}')
        values = list(map(number, row[1:]))
        values_by_code[code] = values
        crosswalk.append(dict(district_code=code, age_source_name=row[0],
                              district_name_th=name, match_method='exact_name_after_prefix_removal'))
        age_values = values[:204]
        male_age = age_values[0::2]
        female_age = age_values[1::2]
        for age in range(102):
            age_records.append(dict(district_code=code, reference_period=PERIOD,
                age_lower=age, age_upper=age if age < 101 else None,
                age_label=str(age) if age < 101 else '101+',
                male=male_age[age], female=female_age[age], total=male_age[age]+female_age[age]))
        special_male = special_female = 0
        for offset, category in enumerate(categories):
            male, female, total = values[204+offset*3:207+offset*3]
            require(male+female == total, f'Special category sex sum {code} {category}')
            special_male += male
            special_female += female
            extras.append(dict(district_code=code, reference_period=PERIOD, category=category,
                               male=male, female=female, total=total))
        require(sum(male_age)+special_male == values[216], f'Male age reconciliation {code}')
        require(sum(female_age)+special_female == values[217], f'Female age reconciliation {code}')
        require(values[216]+values[217] == values[218], f'Age source total {code}')
        require(values[216:219] == [population[code][f] for f in
                ('population_male','population_female','population_total')], f'Age vs population {code}')
        age_total = sum(age_values)
        older = sum(male_age[60:])+sum(female_age[60:])
        summary[code] = dict(age_classified_thai_population=age_total,
            population_age_0_14=sum(male_age[:15])+sum(female_age[:15]),
            population_age_15_59=sum(male_age[15:60])+sum(female_age[15:60]),
            population_age_60_plus=older,
            population_outside_age_series=special_male+special_female,
            age_60_plus_share_of_age_classified_thai=round(older/age_total, 8))
    require(set(values_by_code) == set(population), 'Age district coverage mismatch')
    require([sum(v[i] for v in values_by_code.values()) for i in range(219)] == province_values,
            'District ages do not sum to Bangkok age control')
    return age_records, extras, summary, crosswalk


def load_boundaries(population):
    with zipfile.ZipFile(RAW / 'district_boundaries.zip') as z:
        # Read named members directly; do not extract arbitrary paths from the archive.
        crs = CRS.from_wkt(z.read('district.prj').decode())
        require(crs.to_epsg() == 32647, 'Unexpected boundary CRS')
        require(z.read('district.cst').decode().strip() == 'x-IBM874', 'Unexpected boundary encoding')
        reader = shapefile.Reader(shp=io.BytesIO(z.read('district.shp')),
                                  shx=io.BytesIO(z.read('district.shx')),
                                  dbf=io.BytesIO(z.read('district.dbf')), encoding='cp874')
        transformer = Transformer.from_crs(crs, 4326, always_xy=True)
        boundaries, geometries, projected, repairs, name_corrections = {}, {}, [], [], []
        for record in reader.iterShapeRecords():
            attrs = record.record.as_dict()
            code = attrs['dcode'].strip()
            require(code in population and code not in boundaries, f'Boundary code mismatch {code}')
            name = attrs['dname'].strip().removeprefix('เขต')
            if code == '1024' and name == 'ราษฏร์บูรณะ':
                name_corrections.append({'district_code':code, 'source_name':name,
                    'canonical_name':population[code]['district_name_th'],
                    'reason':'Exact code match; source boundary misspells ราษฎร์บูรณะ'})
                name = population[code]['district_name_th']
            require(name == population[code]['district_name_th'], f'Boundary name mismatch {code}')
            geom = shape(record.shape.__geo_interface__)
            if not geom.is_valid:
                old_area = geom.area
                geom = make_valid(geom)
                repairs.append({'district_code':code,'area_delta_m2':geom.area-old_area})
            require(geom.is_valid and not geom.is_empty and geom.geom_type in ('Polygon','MultiPolygon'),
                    f'Invalid polygon {code}')
            projected.append(geom)
            area = geom.area / 1_000_000
            require(area > 0, f'Invalid area {code}')
            geographic = transform(transformer.transform, geom)
            minx, miny, maxx, maxy = geographic.bounds
            require(100 < minx < maxx < 102 and 13 < miny < maxy < 15, f'Unexpected bounds {code}')
            geometries[code] = mapping(geographic)
            boundaries[code] = dict(district_code=code, district_name_th=name,
                district_name_en=attrs['dname_e'].strip(), area_km2=round(area, 8),
                boundary_resource_date=BOUNDARY_RESOURCE_DATE)
        require(set(boundaries) == set(population), 'Boundary coverage mismatch')
        area_sum = sum(g.area for g in projected)
        area_union = unary_union(projected).area
        return boundaries, geometries, dict(source_crs='EPSG:32647', output_crs='EPSG:4326',
            valid_geometries=len(geometries), geometry_repairs=repairs,
            name_corrections=name_corrections,
            sum_area_km2=area_sum/1e6, union_area_km2=area_union/1e6,
            overlap_area_m2=max(0,area_sum-area_union),
            boundary_resource_date=BOUNDARY_RESOURCE_DATE,
            boundary_effective_date='not specified by source metadata')


def save_database(boundaries, geometry, base, ages, extras, manifest):
    path = OUT / 'bkk_base.sqlite'
    con = sqlite3.connect(path)
    con.execute('PRAGMA foreign_keys=ON')
    with con:
        # Rebuild only the tables owned by this importer, retaining unrelated user tables.
        for table in ('population_age','population_age_exclusions','district_population','sources','districts'):
            con.execute(f'DROP TABLE IF EXISTS {table}')
        con.execute('CREATE TABLE districts (district_code TEXT PRIMARY KEY, district_name_th TEXT NOT NULL, district_name_en TEXT NOT NULL, area_km2 REAL NOT NULL, boundary_resource_date TEXT, geometry_geojson TEXT NOT NULL)')
        for row in boundaries:
            con.execute('INSERT INTO districts VALUES (?,?,?,?,?,?)', tuple(row.values())+(json.dumps(geometry[row['district_code']],ensure_ascii=False),))
        types = {'district_code':'TEXT','district_name_th':'TEXT','district_name_en':'TEXT',
                 'reference_period':'TEXT','boundary_resource_date':'TEXT',
                 'area_km2':'REAL','population_density_per_km2':'REAL',
                 'age_60_plus_share_of_age_classified_thai':'REAL'}
        fields = list(base[0])
        definitions = ','.join(f'"{k}" {types.get(k,"INTEGER")} NOT NULL' for k in fields)
        con.execute(f'CREATE TABLE district_population ({definitions}, PRIMARY KEY(district_code,reference_period), FOREIGN KEY(district_code) REFERENCES districts(district_code))')
        con.executemany(f'INSERT INTO district_population VALUES ({",".join("?" for _ in fields)})',
                        [tuple(r[k] for k in fields) for r in base])
        con.execute('CREATE TABLE population_age (district_code TEXT, reference_period TEXT, age_lower INTEGER, age_upper INTEGER, age_label TEXT, male INTEGER, female INTEGER, total INTEGER, PRIMARY KEY(district_code,reference_period,age_lower), FOREIGN KEY(district_code) REFERENCES districts(district_code))')
        con.executemany('INSERT INTO population_age VALUES (?,?,?,?,?,?,?,?)', [tuple(r.values()) for r in ages])
        con.execute('CREATE TABLE population_age_exclusions (district_code TEXT, reference_period TEXT, category TEXT, male INTEGER, female INTEGER, total INTEGER, PRIMARY KEY(district_code,reference_period,category), FOREIGN KEY(district_code) REFERENCES districts(district_code))')
        con.executemany('INSERT INTO population_age_exclusions VALUES (?,?,?,?,?,?)', [tuple(r.values()) for r in extras])
        con.execute('CREATE TABLE sources (file TEXT PRIMARY KEY, url TEXT, retrieved_at TEXT, sha256 TEXT, metadata_json TEXT)')
        con.executemany('INSERT INTO sources VALUES (?,?,?,?,?)',
            [(r['file'],r['url'],r['retrieved_at'],r['sha256'],json.dumps(r,ensure_ascii=False)) for r in manifest])
    require(con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'SQLite integrity failed')
    require(not con.execute('PRAGMA foreign_key_check').fetchall(), 'SQLite foreign keys failed')
    con.close()


def main():
    manifest = json.loads((RAW/'manifest.json').read_text(encoding='utf-8'))
    for item in manifest:
        require(item['status'] == 'downloaded', f'Incomplete source {item["file"]}')
        path = ROOT / item['file'].replace('\\','/')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], f'Source checksum mismatch {path}')
    population, control = load_population()
    ages, extras, summaries, crosswalk = load_ages(population)
    boundaries, geometries, geometry_report = load_boundaries(population)
    base = []
    for code in sorted(population):
        row = {**boundaries[code], **population[code], **summaries[code]}
        row['population_density_per_km2'] = round(row['population_total']/row['area_km2'], 4)
        base.append(row)
    boundary_rows = [boundaries[c] for c in sorted(boundaries)]
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv('districts.csv', boundary_rows)
    write_csv('district_population_2025.csv', base)
    write_csv('district_population_age_2025.csv', ages)
    write_csv('district_population_age_exclusions_2025.csv', extras)
    write_csv('district_name_crosswalk.csv', crosswalk)
    geojson = {'type':'FeatureCollection','features':[
        {'type':'Feature','id':r['district_code'],'properties':r,'geometry':geometries[r['district_code']]}
        for r in base]}
    (OUT/'districts.geojson').write_text(json.dumps(geojson,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    save_database(boundary_rows, geometries, base, ages, extras, manifest)
    report = dict(reference_period=PERIOD, district_count=len(base), age_row_count=len(ages),
        age_exclusion_row_count=len(extras), bangkok_control=control,
        population_age_60_plus=sum(r['population_age_60_plus'] for r in base),
        age_classified_thai_population=sum(r['age_classified_thai_population'] for r in base),
        population_outside_age_series=sum(r['population_outside_age_series'] for r in base),
        validations={'district_codes_complete':True,'names_match':True,
            'sex_totals_match':True,'district_sums_match_province':True,
            'age_values_match_population_totals':True,'all_age_columns_match_province':True,
            'source_checksums_match':True,'sqlite_integrity_and_foreign_keys':True},
        geometry=geometry_report,
        limitations=[
            'Population is registered population, not resident/daytime population.',
            'Single-year age series covers Thai nationals in house registration as defined by DOPA; four separately reported categories are retained.',
            '60+ share denominator is age-classified Thai population, not all registered population.',
            'Boundary resource date is 2021-03-09; effective boundary date is not specified. No current legal-boundary verification was performed.',
            'Area is calculated from source polygons in EPSG:32647, not an official statistical area.',
            'Source shapefile demographic attributes are ignored because their period is unspecified.'
        ])
    (OUT/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
