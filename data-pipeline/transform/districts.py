import importlib.util
from pathlib import Path
import geopandas as gpd

ROOT=Path(__file__).resolve().parents[2]

def build_base():
    # Reuse the validated original parser; rebuild derived files from preserved originals.
    spec=importlib.util.spec_from_file_location('base_import',ROOT/'scripts/import_base_data.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.main()
    frame=gpd.read_file(ROOT/'data/processed/districts.geojson')
    if len(frame)!=50 or frame.district_code.nunique()!=50:raise ValueError('Expected 50 unique districts')
    if frame.crs.to_epsg()!=4326 or not frame.geometry.is_valid.all():raise ValueError('Invalid district geometries/CRS')
    return frame

