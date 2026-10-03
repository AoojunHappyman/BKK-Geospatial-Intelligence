import {test,expect} from '@playwright/test';

test('top and bottom five use the selected zone and preserve zero values',async({page})=>{
 await page.goto('/?metric=transit_station_count');
 await page.getByLabel('กลุ่มเขต',{exact:true}).selectOption('กรุงเทพใต้');
 await expect(page.locator('.stat').first()).toContainText('10');
 await expect(page.locator('.rank-row')).toHaveCount(5);
 const rows=await (await page.request.get('/api/districts')).json();
 const expected=rows.filter((r:any)=>r.zone==='กรุงเทพใต้').sort((a:any,b:any)=>a.transit_station_count-b.transit_station_count||a.district_code.localeCompare(b.district_code)).slice(0,5);
 await page.getByRole('button',{name:'ต่ำสุด 5 อันดับ'}).click();
 await expect.poll(()=>page.locator('.rank-row').evaluateAll(a=>a.map(el=>new URL((el as HTMLAnchorElement).href).pathname.split('/').pop()))).toEqual(expected.map((r:any)=>r.district_code));
 await page.reload();await expect(page.getByRole('button',{name:'ต่ำสุด 5 อันดับ'})).toHaveAttribute('aria-pressed','true');
 await expect(page.getByLabel('กลุ่มเขต',{exact:true})).toHaveValue('กรุงเทพใต้');
});

test('all table columns sort, and export exactly matches filtered table order',async({page})=>{
 await page.goto('/districts?zone=กรุงเทพเหนือ');
 await expect(page.locator('tbody tr')).toHaveCount(7);
 await page.getByRole('button',{name:'พื้นที่ (ตร.กม.)',exact:false}).click();
 await expect(page.locator('th').nth(2)).toHaveAttribute('aria-sort','descending');
 const areas=await page.locator('tbody tr td:nth-child(3)').allTextContents();
 expect(areas.map(v=>Number(v.replaceAll(',','')))).toEqual(areas.map(v=>Number(v.replaceAll(',',''))).sort((a,b)=>b-a));
 for(const label of ['เขต / District','ประชากร','เปรียบเทียบ']){
  await page.locator('thead').getByRole('button',{name:new RegExp('^'+label+' ')}).click();
 }
 await page.locator('thead').getByRole('button',{name:'เขต / District',exact:false}).click();
 await expect(page.locator('th').first()).toHaveAttribute('aria-sort','ascending');
 const order=await page.locator('tbody tr').evaluateAll(rows=>rows.map(r=>r.getAttribute('data-district')));
 const href=(await page.getByRole('link',{name:'ส่งออก CSV ตามตัวกรอง'}).getAttribute('href'))!;
 const csv=await (await page.request.get(href)).text();
 expect(csv.trim().split(/\r?\n/).slice(1).map(line=>line.split(',')[0])).toEqual(order);
 await page.getByLabel('ค้นหาเขต',{exact:true}).fill('ไม่พบเขตนี้');
 await expect(page.getByRole('link',{name:'ส่งออก CSV ตามตัวกรอง'})).toHaveAttribute('href','/api/export/districts.csv?districts=');
 const empty=(await page.getByRole('link',{name:'ส่งออก CSV ตามตัวกรอง'}).getAttribute('href'))!;
 expect((await (await page.request.get(empty)).text()).trim().split(/\r?\n/)).toHaveLength(1);
});

test('profile shows real age-sex bands, city benchmark, and point list drives map',async({page})=>{
 await page.goto('/district/1007');
 await expect(page.locator('.pyramid-row')).toHaveCount(21);
 await expect(page.locator('.benchmark-grid')).toContainText('ประชากรรวม ÷ พื้นที่รวมทั้ง 50 เขต');
 await page.getByRole('button',{name:'บริการสุขภาพ',exact:true}).click();
 const health=await (await page.request.get('/api/districts/1007/infrastructure')).json();
 const name=health.features[0].properties.name;
 const poi=page.locator('.point-list').getByRole('button',{name:name+' ↗',exact:true});
 await expect(poi).toBeVisible();
 await poi.click();
 await expect(page.locator('.maplibregl-popup-content')).toContainText(name);
 await expect.poll(async()=>Number(await page.locator('.map').getAttribute('data-zoom'))).toBeCloseTo(15,0);
 await page.getByRole('button',{name:'น้ำท่วม 2565',exact:true}).click();
 await expect(page.locator('.maplibregl-popup')).toHaveCount(0);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});
