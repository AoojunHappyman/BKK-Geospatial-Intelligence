import csv,io,json,math
from extract.sources import read_snapshot

def transform_points(source_id,info,osm=None):
    records=[];rejected=[];seen=set()
    coordinate_index={}
    if osm:
        for part in osm['parts']:
            for element in json.loads(read_snapshot(part['path'],part['sha256']))['elements']:
                if element['type']=='node' and element.get('tags',{}).get('railway')=='station':
                    ref=element['tags'].get('ref','').strip()
                    coordinate_index.setdefault(ref,[]).append(element)
    for part in info['parts']:
        raw=read_snapshot(part['path'],part['sha256'])
        if info['type']=='csv':
            rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
            required={'Line_Code','Station_Code','Latitude','Longitude','Status','Station_Name_TH'}
            if not rows or not required.issubset(rows[0]):raise ValueError('Transit columns missing')
            for row in rows:
                rid=f"{row['Line_Code']}:{row['Station_Code']}"
                if row['Status'].strip()!='1':
                    rejected.append(dict(id=rid,reason='not_status_1'));continue
                props={'status':row['Status'],'name_en':row.get('Station_Name_EN'),'coordinate_source':'transit'}
                if not row['Longitude'] or not row['Latitude']:
                    matches=coordinate_index.get(row['Station_Code'].strip(),[])
                    if len(matches)==1:
                        row['Longitude']=matches[0]['lon'];row['Latitude']=matches[0]['lat']
                        props.update(coordinate_source='osm_transit',osm_node_id=matches[0]['id'])
                records.append(dict(id=rid,name=row['Station_Name_TH'].strip(),category=row['Line_Code'].strip(),
                    lon=row['Longitude'],lat=row['Latitude'],properties={'status':row['Status'],'name_en':row.get('Station_Name_EN')}))
                records[-1]['properties']=props
        else:
            doc=json.loads(raw)
            if doc.get('spatialReference',{}).get('wkid') not in (4326,None):raise ValueError('Point response must be WGS84')
            for feature in doc['features']:
                a=feature['attributes'];g=feature.get('geometry') or {}
                records.append(dict(id=str(a['OBJECTID']),name=str(a.get(info['name_field']) or '').strip(),
                    category=str(a.get(info.get('category_field')) or info.get('category') or 'จุดน้ำท่วม'),
                    lon=g.get('x'),lat=g.get('y'),properties=a))
    clean=[]
    for r in records:
        if r['id'] in seen:raise ValueError(f'Duplicate source id {source_id}/{r["id"]}')
        seen.add(r['id'])
        try:
            r['lon']=float(r['lon']);r['lat']=float(r['lat'])
            if not math.isfinite(r['lon']) or not math.isfinite(r['lat']) or not (99<r['lon']<102 and 12<r['lat']<15):raise ValueError()
        except (ValueError,TypeError):
            rejected.append(dict(id=r['id'],reason='invalid_coordinates'));continue
        if not r['name']:r['name']=f"{info['name']} #{r['id']}"
        clean.append(r)
    invalid=sum(r['reason']=='invalid_coordinates' for r in rejected)
    if invalid/max(len(records),1)>.02:raise ValueError(f'Too many invalid coordinates: {source_id}')
    if not clean:raise ValueError(f'No valid points: {source_id}')
    return clean,dict(accepted=len(clean),osm_coordinates=sum(r['properties'].get('coordinate_source')=='osm_transit' for r in clean),rejected=rejected)

