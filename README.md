# BKK Geospatial Intelligence

แพลตฟอร์มวิเคราะห์เมืองระดับ **50 เขตกรุงเทพมหานคร** ใช้ข้อมูลจริงจาก กทม., DOPA, กรมการขนส่งทางราง และ OpenStreetMap ผ่าน Python ETL, PostgreSQL/PostGIS, FastAPI และ React/TypeScript/MapLibre

![Overview](docs/screenshots/overview.png)

## ใช้งานอะไรได้

- Overview: แผนที่ choropleth ครบ 50 เขต สลับ 8 ตัวชี้วัด พร้อมอันดับคำนวณจากฐานข้อมูล
- District Explorer: ค้นหาและสำรวจเขตผ่านแผนที่และตาราง
- District Profile: ประชากร กลุ่มอายุ การเดินทาง ศูนย์สุขภาพ และจุดปัญหาน้ำท่วมรายเขต
- District Compare: เปรียบเทียบ 2–4 เขตผ่านกราฟและค่าจริง
- Data Explorer: ดูแหล่งที่มา ช่วงข้อมูล วันที่นำเข้า checksum วิธีคำนวณ และดาวน์โหลดตาราง CSV

### สำรวจต่อเนื่องและแชร์มุมมอง

คลิกเขตในแผนที่ Overview, Explorer หรือ Data Explorer เพื่อเปิดแผงรายละเอียดและเน้นขอบเขต โดยไม่เปลี่ยนหน้าและไม่ซูมออกจากมุมมองเดิม เพิ่ม/นำเขตออกจากชุดเปรียบเทียบได้จากแผง ตาราง และหน้าโปรไฟล์ แถบด้านล่างเก็บชุดเดียวกันตลอดการเปลี่ยนหน้าผ่านเมนู และเปิด Compare ได้เมื่อเลือก 2–4 เขต

ปุ่ม “แชร์มุมมองนี้” คัดลอก URL ซึ่งเก็บตัวชี้วัด (`metric`), เขตที่เปิด (`district`), ชุดเปรียบเทียบ (`districts`), คำค้น (`q`), แหล่งข้อมูล (`source`) และชั้นข้อมูลโปรไฟล์ (`layer`) ตามหน้าที่ใช้งาน รองรับ reload, browser back/forward และเปิดลิงก์บนเครื่องอื่นที่เข้าถึงเว็บได้ รหัสเขตที่ไม่รู้จัก/ซ้ำถูกละเว้นและจำกัดชุดเปรียบเทียบสูงสุด 4 เขต มุมกล้องที่ผู้ใช้ลาก/ซูมเองยังไม่บันทึกใน URL ลิงก์ localhost ใช้ได้บนเครื่องที่รัน demo เท่านั้น

![Exploration and comparison flow](docs/screenshots/explore-flow.png)

ข้อมูลที่นำเข้า: ประชากรทะเบียน ธ.ค. 2568 รวม 5,422,568 คน; สถานีแยกตามสาย 195 รายการ (อยู่ในกรุงเทพฯ 152); ศูนย์บริการสาธารณสุข 69 แห่ง; จุดปัญหาน้ำท่วมจากการถอดบทเรียนปี 2565 จำนวน 737 จุด ข้อมูลแต่ละชุดเป็นคนละช่วงเวลา ไม่มีการอ้างว่าเป็นสถานการณ์สด

## Architecture

```mermaid
flowchart LR
  S[DOPA · BMA · DRT · OSM] --> R[Immutable raw + SHA256]
  R --> E[Python validation / GeoPandas]
  E --> P[PostgreSQL + PostGIS]
  P --> M[Spatial joins + metric materialized view]
  M --> A[FastAPI]
  A --> U[React + MapLibre]
```

ขอบเขตและจุดเก็บใน EPSG:4326; คำนวณพื้นที่/รัศมีใน EPSG:32647; ค้นหาใกล้เคียงใช้ PostGIS geography หน่วยเมตร Frontend ขอข้อมูลวิเคราะห์ผ่าน API ทุกหน้า ไม่มีการอ่าน CSV เพื่อสร้างอันดับใน browser

## รันบนเครื่องนี้ (Windows)

เครื่องนี้ติดตั้ง runtime และฐานข้อมูลแบบ portable ไว้ในโฟลเดอร์ที่ gitignore แล้ว:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

เปิด <http://127.0.0.1:5173> และเอกสาร API <http://127.0.0.1:8000/docs> สคริปต์เริ่มบริการที่ยังไม่ทำงานเท่านั้น ปิดบริการที่สคริปต์เปิดด้วย `scripts/stop-local.ps1` ฐานข้อมูล local นี้ใช้ trust authentication จำกัดฟังเฉพาะ localhost สำหรับ demo เท่านั้น

## ติดตั้งใหม่ด้วย PostgreSQL/PostGIS

ต้องมี Python 3.13, Node.js 24 และ PostgreSQL 17 พร้อม PostGIS ติดตั้งอยู่ สร้างฐานข้อมูล `bkk` และผู้ใช้ที่มีสิทธิ์สร้าง extension สำหรับขั้น ETL

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r data-pipeline/requirements.txt
$env:DATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:5432/bkk'
python data-pipeline/pipeline.py
python scripts/run_api.py
```

เปิดอีก terminal:

```powershell
cd frontend
npm ci
npm run dev
```

บน Linux/macOS ใช้ `source .venv/bin/activate` และ `export DATABASE_URL=...` แทน PowerShell ค่าเริ่มต้น ETL ใช้ snapshot ที่เก็บไว้ จึงไม่ต้องพึ่งเว็บต้นทางตอนรันซ้ำ `python data-pipeline/pipeline.py --refresh` ดาวน์โหลดชุดข้อมูลจุดใหม่ โดยเก็บ snapshot เดิมไว้ ข้อมูลประชากร/ขอบเขตผูกกับปีฐาน หากจะเปลี่ยนปีต้องปรับ extractor และตรวจนิยามก่อน

เครื่อง Windows ที่ไม่มี PostgreSQL สามารถใช้ `scripts/download_dev_database.py` และ `scripts/unpack_database.py` เพื่อเตรียม binary แบบ portable จากนั้น `initdb -D .local/pgdata -U bkk -A trust -E UTF8 --locale=C`, เริ่ม pg_ctl ฟัง localhost port 55432 และ `createdb -h 127.0.0.1 -p 55432 -U bkk bkk` ก่อนนำเข้า ดู path binary ใน `.local/pgsql/bin` ต้องใช้ trust เฉพาะ demo บนเครื่องส่วนตัว

## Docker

```powershell
Copy-Item .env.example .env
# แก้ POSTGRES_PASSWORD ใน .env ใช้ค่าสุ่มที่ URL-safe
docker compose up --build -d
```

เปิด <http://127.0.0.1:8080> ลำดับเริ่มคือ PostGIS → ETL → API → Nginx/Frontend ข้อมูล DB อยู่ใน named volume อย่าใช้ `down -v` หากต้องการเก็บข้อมูล

**ข้อจำกัดการตรวจสอบ:** เครื่องพัฒนานี้ไม่มี Docker จึงยังไม่ได้รัน Compose จริง ไฟล์ Docker/CI เตรียมไว้แล้ว แต่ยังไม่ถือว่าผ่านการทดสอบบน container รายละเอียดใน [verification](docs/verification.md)

## ทดสอบ

ตั้ง `DATABASE_URL` ให้ชี้ฐานข้อมูลที่นำเข้าแล้ว จาก root:

```powershell
python scripts/test_backend.py
cd frontend
npm run build
npm test
```

Browser tests ใช้ Microsoft Edge บน Windows; CI ใช้ Chromium ผ่าน Playwright (`npx playwright install --with-deps chromium`) Tests ตรวจฐานข้อมูลจริง การรวมยอด ขอบเขต/CRS การคำนวณระยะ การแสดง polygon ครบ 50 เขต การเปรียบเทียบ CSV และสถานะ error/empty/mobile ไม่ mock ค่าสถิติ

## โครงสร้างและเอกสาร

| Path | หน้าที่ |
|---|---|
| `data/raw`, `data/processed` | ต้นฉบับ immutable / ผลแปลงและ validation reports |
| `data-pipeline/` | extract → transform → transactional load |
| `database/` | schema, indexes, SQL aggregates, spatial query examples |
| `backend/` | FastAPI และ integration tests |
| `frontend/` | React, MapLibre และ browser tests |
| `docs/PROJECT_SPEC.md` | ข้อกำหนดฉบับเต็มจากผู้ใช้ |
| [Architecture](docs/architecture.md) | ตารางฐานข้อมูลและ API |
| [Methodology](docs/methodology.md) | สูตร นิยาม ข้อจำกัด |
| [Sources](docs/data-sources.md) | แหล่งข้อมูลและสิทธิ์การใช้ |
| [Base data](data/README.md) | รายละเอียดประชากร/อายุและการกระทบยอด |

![District comparison](docs/screenshots/compare.png)

MVP ยังไม่มีข้อมูลย้อนหลังหลายปี, เวลาเดินตามโครงข่ายถนน, ความจุบริการ, ML หรือคะแนนรวมความน่าอยู่อาศัย การเปรียบเทียบมีไว้สำรวจหลักฐานและข้อจำกัด ไม่ได้ตัดสินว่าเขตใดดีที่สุด
