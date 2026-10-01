import {test,expect} from '@playwright/test';

test('overview, metric selection, explorer and profile use API data',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.getByRole('heading',{name:'มองกรุงเทพฯ ผ่านข้อมูล'})).toBeVisible();
 await expect(page.getByText('5,422,568',{exact:true})).toBeVisible();
 await expect(page.locator('.maplibregl-canvas')).toBeVisible();
 await expect(page.locator('.map')).toHaveAttribute('data-rendered-districts','50');
 await page.getByLabel('ตัวชี้วัด',{exact:true}).selectOption('transit_coverage');
 await expect(page.locator('.map-legend')).toContainText('พื้นที่ใกล้รถไฟฟ้า');
 const bounds=await page.locator('.maplibregl-canvas').boundingBox();
 await page.mouse.click(bounds!.x+bounds!.width/2,bounds!.y+bounds!.height/2);
 await expect(page).toHaveURL(/district=10\d{2}/);
 await expect(page.getByRole('complementary',{name:'รายละเอียดเขตที่เลือก'})).toBeVisible();
 await page.goto('/districts');await page.getByLabel('ค้นหาเขต',{exact:true}).fill('ปทุมวัน');
 await expect(page.locator('tbody tr')).toHaveCount(1);
 await page.locator('tbody tr a').first().click();
 await expect(page).toHaveURL(/district\/1007/);
 await expect(page.getByRole('heading',{name:'ปทุมวัน',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'บริการสุขภาพ',exact:true}).click();
 await expect(page.locator('.source-note').first()).toContainText('ศูนย์บริการสาธารณสุข');
 expect(errors).toEqual([]);
});

test('loading state resolves when API finishes',async({page})=>{
 let release!:()=>void;
 const gate=new Promise<void>(resolve=>{release=resolve;});
 await page.route('**/api/districts',async route=>{await gate;await route.continue();});
 await page.goto('/');
 await expect(page.getByRole('status')).toContainText('กำลังโหลดข้อมูล');
 release();
 await expect(page.getByRole('heading',{name:'มองกรุงเทพฯ ผ่านข้อมูล'})).toBeVisible();
});

test('comparison enforces 2–4 districts and renders computed bars',async({page})=>{
 await page.goto('/compare');
 await expect(page.getByText('เริ่มจากสองเขตที่คุณสนใจ')).toBeVisible();
 for(const id of ['1007','1030','1001','1011']){
  await page.getByLabel('เพิ่มเขต',{exact:true}).selectOption(id);
  await page.getByRole('button',{name:'เพิ่มเขต',exact:false}).click();
 }
 await expect(page.locator('.selected-chips button')).toHaveCount(4);
 await expect(page.locator('.comparison-grid .panel')).toHaveCount(5);
 await expect(page.getByRole('button',{name:'เพิ่มเขต',exact:false})).toBeDisabled();
 await page.locator('.selected-chips button').first().click();
 await expect(page.locator('.selected-chips button')).toHaveCount(3);
});

test('data provenance and CSV export',async({page})=>{
 await page.goto('/data');await page.getByLabel('ชุดข้อมูล',{exact:true}).selectOption('risk');
 await expect(page.locator('.dataset-card')).toContainText('2565');
 await expect(page.getByLabel('ช่วงข้อมูล')).toHaveValue('2022 (2565)');
 const response=await page.request.get('/api/export/districts.csv');
 expect(response.ok()).toBeTruthy();expect((await response.text()).split('\n').filter(Boolean)).toHaveLength(51);
});

test('API failure is visible with retry',async({page})=>{
 await page.route('**/api/districts',route=>route.fulfill({status:503,body:'{}'}));
 await page.goto('/');await expect(page.getByRole('alert')).toContainText('ไม่สามารถโหลดข้อมูล');
 await expect(page.getByRole('button',{name:'ลองใหม่'})).toBeVisible();
});

test('mobile has no horizontal overflow and searchable districts',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/districts');
 await expect(page.getByRole('heading',{name:'ทุกเขตมีเรื่องราว'})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.getByLabel('ค้นหาเขต',{exact:true}).fill('xyz-no-district');
 await expect(page.getByText('ไม่พบเขตที่ตรงกับคำค้น')).toBeVisible();
});
