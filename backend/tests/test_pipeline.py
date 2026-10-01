import json
from extract.sources import load_sources,ROOT
from transform.points import transform_points

def test_snapshot_checksums_and_real_points():
    catalog=load_sources()
    for source,count in [('transit',195),('healthcare',69),('risk',737)]:
        rows,report=transform_points(source,catalog[source],catalog.get('osm_transit'))
        assert len(rows)==count
        assert len({r['id'] for r in rows})==count
        assert all(99<r['lon']<102 and 12<r['lat']<15 for r in rows)
        assert not any(r['reason']=='invalid_coordinates' for r in report['rejected'])
    _,report=transform_points('transit',catalog['transit'],catalog['osm_transit'])
    assert report['osm_coordinates']==55

def test_pinned_population_reconciliation():
    import importlib.util
    spec=importlib.util.spec_from_file_location('base',ROOT/'scripts/import_base_data.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    pop,control=mod.load_population()
    ages,extras,summaries,crosswalk=mod.load_ages(pop)
    assert len(ages)==5100 and len(extras)==200 and len(crosswalk)==50
    assert sum(s['age_classified_thai_population']+s['population_outside_age_series'] for s in summaries.values())==control['population_total']

