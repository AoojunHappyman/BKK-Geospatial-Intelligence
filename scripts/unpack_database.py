from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'.local';dest.mkdir(exist_ok=True)
for filename in ['postgres.zip','postgis.zip']:
 with zipfile.ZipFile(ROOT/'.cache'/filename) as z:
  print(filename,z.namelist()[:12],flush=True)
  for info in z.infolist():
   parts=Path(info.filename).parts
   if filename=='postgres.zip':
    if len(parts)<2 or parts[1] not in ('bin','lib','share'):continue
    relative=Path(*parts)
   else:
    # PostGIS archive has one bundle directory containing bin/lib/share.
    if len(parts)<2 or parts[1] not in ('bin','lib','share'):continue
    relative=Path('pgsql',*parts[1:])
   target=(dest/relative).resolve()
   if not target.is_relative_to(dest.resolve()):raise ValueError('Unsafe archive path')
   if info.is_dir():target.mkdir(parents=True,exist_ok=True)
   else:
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(info))
print('Portable database unpacked',flush=True)
