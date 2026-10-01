METRICS = [
 dict(id='population_density',label='ความหนาแน่นประชากร',label_en='Population density',unit='คน / ตร.กม.',dimension='Demographics',sources=['population','districts'],period='2025-12',decimals=0,description='ประชากรทะเบียน ÷ พื้นที่ polygon คำนวณใน EPSG:32647'),
 dict(id='population_total',label='ประชากรทะเบียน',label_en='Registered population',unit='คน',dimension='Demographics',sources=['population'],period='2025-12',decimals=0,description='ประชากรตามทะเบียน ไม่ใช่ประชากรกลางวันหรือจำนวนผู้พักอาศัยจริง'),
 dict(id='older_share',label='สัดส่วนอายุ 60+',label_en='Age 60+ share',unit='%',dimension='Demographics',sources=['population_age'],period='2025-12',decimals=1,description='ผู้มีอายุ 60+ ÷ ประชากรไทยในชุดแจกแจงอายุ × 100 ไม่รวมกลุ่มที่ต้นทางแยกไว้'),
 dict(id='transit_coverage',label='พื้นที่ใกล้รถไฟฟ้า 800 ม.',label_en='Rail proximity',unit='%',dimension='Mobility',sources=['transit','osm_transit','districts'],period='snapshot',decimals=1,description='สัดส่วนพื้นที่เขตในรัศมีเส้นตรง 800 เมตรจากสถานี รวมสถานีนอกเขต ไม่ใช่เวลาเดินหรือสัดส่วนประชากร'),
 dict(id='transit_station_count',label='สถานีแยกตามสาย',label_en='Rail station records',unit='สถานี-สาย',dimension='Mobility',sources=['transit'],period='snapshot',decimals=0,description='นับรหัสสถานีร่วมกับสาย สถานีเปลี่ยนสายอาจมีมากกว่าหนึ่งรายการ กรอง Status=1 ตามข้อมูลต้นทาง'),
 dict(id='healthcare_per_100k',label='ศูนย์สุขภาพต่อแสนคน',label_en='Health centers / 100k',unit='แห่ง / แสนคน',dimension='Infrastructure',sources=['healthcare','population'],period='mixed',decimals=2,description='ศูนย์บริการสาธารณสุขในชุดข้อมูล กทม. ÷ ประชากร ธ.ค. 2568 × 100,000 ไม่ครอบคลุมสถานพยาบาลทุกประเภท'),
 dict(id='healthcare_facility_count',label='ศูนย์บริการสาธารณสุข',label_en='Public health centers',unit='แห่ง',dimension='Infrastructure',sources=['healthcare'],period='snapshot',decimals=0,description='จำนวนรายการศูนย์บริการสาธารณสุขในชุดข้อมูล กทม. ไม่ใช่ความจุหรือคุณภาพบริการ'),
 dict(id='risk_location_count',label='จุดปัญหาน้ำท่วม 2565',label_en='Flood locations · 2022',unit='จุด',dimension='Urban Risk',sources=['risk'],period='2022',decimals=0,description='จำนวนจุดจากการถอดบทเรียนน้ำท่วมปี 2565 ไม่ใช่ความเสี่ยงปัจจุบันหรือความน่าจะเป็น ค่าศูนย์หมายถึงไม่มีรายการในชุดนี้'),
]
METRIC_IDS = {m['id'] for m in METRICS}

