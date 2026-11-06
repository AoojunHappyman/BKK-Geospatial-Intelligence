# Vercel + Neon

## สภาพแวดล้อมปัจจุบัน

- เว็บ Production: <https://bkkgeo.vercel.app/>
- Vercel project: `bkk-geospatial-intelligence` ในทีม `aoo2` ใช้แผน Hobby
- โดเมนเดิม `bkk-geospatial-intelligence.vercel.app` ตั้ง redirect ไป `bkkgeo.vercel.app`
- Neon project: `bkkgeo`, branch `production`, database `neondb`, ภูมิภาค Singapore ใช้แผน Free
- เปิด PostGIS แล้ว นำเข้าครบ 50 เขต / ประชากร 5,422,568 คน และสร้างบัญชีอ่านอย่างเดียว `bkk_api` แล้ว

สถานะอ้างอิงการตั้งค่าและผลตรวจเมื่อ 7 พฤศจิกายน 2569 Vercel แสดงผล deploy สำเร็จแล้ว ส่วนการตรวจ API และข้อมูลบนโดเมนจริงให้ทำตามรายการท้ายเอกสาร

## ตั้งค่า Vercel

Import repository `AoojunHappyman/BKK-Geospatial-Intelligence` สาขา `main` โดยใช้ root ของ repository:

| การตั้งค่า | ค่า |
|---|---|
| Root Directory | `./` |
| Application Preset | `Other` |
| Install Command | `npm ci --prefix frontend` |
| Build Command | `npm run build --prefix frontend` |
| Output Directory | `frontend/dist` |

ค่า build อยู่ใน `vercel.json` ซึ่งส่ง `/api/*` ไปที่ Python ASGI function `api/index.py` และส่งเส้นทางหน้าเว็บไปที่ React SPA อย่าแยก import `frontend`, `backend` หรือ `data-pipeline` เป็น Services สำหรับ configuration นี้

เพิ่ม environment variable ฝั่ง server:

| Key | Value |
|---|---|
| `DATABASE_URL` | Connection string ของ Neon role `bkk_api` ที่เปิด Connection pooling และใช้ TLS |

ใส่ URL ทั้งหมดในช่อง **Value** โดยชื่อ **Key** ต้องเป็น `DATABASE_URL` อย่าใช้บัญชี owner สำหรับ API, อย่าเติม `VITE_` หน้าชื่อ และอย่า commit รหัสผ่านหรือ Connection string จริงลง Git หลังเปลี่ยน environment variable ให้ deploy ใหม่เพื่อให้บริการใช้ค่าใหม่

## นำเข้าและอัปเดตข้อมูล

ETL ทำงานจากเครื่องผู้ดูแลด้วยบัญชี owner ที่เขียนข้อมูลได้ ส่วน Vercel ทำหน้าที่อ่านฐานข้อมูลเท่านั้น ติดตั้ง dependencies จาก `data-pipeline/requirements.txt` แล้วตั้ง `DATABASE_URL` ใน environment ของ terminal ให้เป็น Connection string ของ owner ก่อนรัน:

```powershell
python data-pipeline/pipeline.py
```

ใช้ snapshot ที่มีใน repository เป็นค่าเริ่มต้น ดูรายละเอียดการ refresh ใน [README](../README.md) ETL dependencies และ raw data ถูกยกเว้นจาก Vercel deployment

บัญชี `bkk_api` มี `CONNECT`, `USAGE` schema และ `SELECT` ตาราง พร้อม `default_transaction_read_only=on` และ default privileges สำหรับตารางใหม่ที่สร้างโดย owner เดิม ถ้าเปลี่ยน owner หรือเพิ่ม schema ต้องตรวจ grants อีกครั้ง สคริปต์ `scripts/configure_api_role.py` สำหรับ PostgreSQL ที่ดูแลเองมีคำสั่งเปลี่ยนคุณสมบัติ role ซึ่งต้องตรวจความเข้ากันได้ก่อนใช้กับ managed Postgres

## ตรวจหลัง deploy

1. เปิด <https://bkkgeo.vercel.app/api/health> ต้องได้ `status: "ok"` และ `districts: 50`
2. เปิด <https://bkkgeo.vercel.app/api/districts> ต้องได้ข้อมูล 50 เขต
3. เปิดหน้าเว็บ ตรวจแผนที่ ตัวชี้วัด โปรไฟล์ และการเปรียบเทียบ ให้โหลดข้อมูลสำเร็จ
4. เปิด `/district/1001` โดยตรงและ reload เพื่อตรวจ SPA routing
5. เปิดโดเมนเดิมเพื่อตรวจ redirect และตรวจว่าโดเมนใหม่ใช้ HTTPS ได้

หาก build ผ่านแต่ API ตอบ 503 ให้ตรวจ runtime logs, `DATABASE_URL`, รหัสผ่านและสิทธิ์ของ `bkk_api` รวมถึงสถานะฐานข้อมูลใน Neon โดยไม่เผยแพร่ Connection string ในภาพหรือ log
