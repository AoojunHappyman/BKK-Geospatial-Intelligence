"""python data-pipeline/pipeline.py [--refresh] [--extract-only]"""
from pathlib import Path
import sys,os,json,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.runtime'))
from extract.sources import refresh_sources,load_sources
from transform.points import transform_points

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--refresh',action='store_true',help='Download new point snapshots; originals remain immutable')
    parser.add_argument('--extract-only',action='store_true')
    args=parser.parse_args()
    catalog=refresh_sources() if args.refresh else load_sources()
    points={};reports={}
    for source_id,info in catalog.items():
        if source_id=='osm_transit':continue
        points[source_id],reports[source_id]=transform_points(source_id,info,catalog.get('osm_transit'))
    if args.extract_only:
        print(json.dumps(reports,ensure_ascii=False,indent=2));return
    if not os.environ.get('DATABASE_URL'):raise SystemExit('Set DATABASE_URL first')
    from transform.districts import build_base
    from load.postgres import load_all
    print(json.dumps(load_all(build_base(),catalog,points,reports),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
