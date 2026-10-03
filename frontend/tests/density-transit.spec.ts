import {test,expect} from '@playwright/test';

test('scatter uses API values and links selection both ways with the map and URL',async({page})=>{
 await page.goto('/?metric=transit_coverage');
 const chart=page.locator('.density-transit');
 await expect(chart.locator('.scatter-point')).toHaveCount(50);
 const rows=await (await page.request.get('/api/districts')).json();
 const density=rows.reduce((s:number,r:any)=>s+r.population_density,0)/50;
 const coverage=rows.reduce((s:number,r:any)=>s+r.transit_coverage,0)/50;
 const expected=rows.filter((r:any)=>r.population_density>density&&r.transit_coverage<coverage).map((r:any)=>r.district_code).sort();
 expect(await chart.locator('.scatter-point.candidate').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-district')).sort())).toEqual(expected);
 const row=rows.find((r:any)=>r.district_code==='1007');
 const point=chart.locator('.scatter-point[data-district="1007"]');
 const dot=point.locator('.scatter-dot');
 expect(Number(await dot.getAttribute('cx'))).toBeCloseTo(80+row.transit_coverage*6.6,4);
 const max=Math.max(5000,Math.ceil(Math.max(...rows.map((r:any)=>r.population_density))/5000)*5000);
 expect(Number(await dot.getAttribute('cy'))).toBeCloseTo(360-row.population_density/max*300,4);
 await point.click();
 await expect(point).toHaveAttribute('aria-pressed','true');
 await expect(page).toHaveURL(/district=1007/);
 await expect(page.getByRole('complementary',{name:'รายละเอียดเขตที่เลือก'})).toContainText('ปทุมวัน');
 await chart.getByRole('button',{name:'ดูเขตที่เลือกบนแผนที่'}).click();
 await expect(page.locator('.map')).toHaveAttribute('data-rendered-districts','50');
 const canvas=await page.locator('.maplibregl-canvas').boundingBox();
 await page.locator('.maplibregl-canvas').click({position:{x:canvas!.width/2,y:canvas!.height/2}});
 await expect.poll(()=>new URL(page.url()).searchParams.get('district')).not.toBe('1007');
 const code=new URL(page.url()).searchParams.get('district')!;
 await expect(chart.locator(`.scatter-point[data-district="${code}"]`)).toHaveAttribute('aria-pressed','true');
 await page.reload();
 await expect(chart.getByLabel('เลือกเขตบนกราฟ',{exact:true})).toHaveValue(code);
 await page.goBack();
 await expect(point).toHaveAttribute('aria-pressed','true');
 await page.getByRole('button',{name:'ปิดรายละเอียดเขต'}).click();
 await expect(chart.locator('.scatter-point[aria-pressed="true"]')).toHaveCount(0);
});

test('scatter supports zone filtering, keyboard and mobile without page overflow',async({page})=>{
 await page.goto('/');
 const chart=page.locator('.density-transit');
 await expect(chart.locator('.scatter-point')).toHaveCount(50);
 const meanLines=await chart.locator('.scatter-mean').evaluateAll(nodes=>nodes.map(n=>n.outerHTML));
 await chart.screenshot({path:'../docs/screenshots/density-transit-desktop.png'});
 await page.getByLabel('กลุ่มเขต',{exact:true}).selectOption('กรุงเทพเหนือ');
 await expect(chart.locator('.scatter-point')).toHaveCount(7);
 expect(await chart.locator('.scatter-mean').evaluateAll(nodes=>nodes.map(n=>n.outerHTML))).toEqual(meanLines);
 const point=chart.locator('.scatter-point').first();
 const code=await point.getAttribute('data-district');
 await point.focus();await page.keyboard.press('Enter');
 await expect(chart.getByLabel('เลือกเขตบนกราฟ',{exact:true})).toHaveValue(code!);
 await page.setViewportSize({width:390,height:844});
 await chart.getByLabel('เลือกเขตบนกราฟ',{exact:true}).selectOption('1030');
 await expect(chart.locator('.scatter-selection')).toContainText('จตุจักร');
 await expect(chart.locator('.scatter-detail h3')).toHaveText('จตุจักร');
 await expect.poll(()=>chart.evaluate(el=>{
  const viewport=el.querySelector('.scatter-scroll')!.getBoundingClientRect();
  const dot=el.querySelector('.scatter-point.selected .scatter-dot')!.getBoundingClientRect();
  return dot.left>=viewport.left&&dot.right<=viewport.right;
 })).toBeTruthy();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await chart.screenshot({path:'../docs/screenshots/density-transit-mobile.png'});
 await page.getByLabel('กลุ่มเขต',{exact:true}).selectOption('กรุงเทพใต้');
 await expect(chart.locator('.scatter-point')).toHaveCount(10);
 await expect(chart.getByLabel('เลือกเขตบนกราฟ',{exact:true})).toHaveValue('');
});

test('missing values are excluded while zero coverage remains a selectable point',async({page})=>{
 await page.route('**/api/districts',async route=>{
  const response=await route.fetch();const rows=await response.json();
  rows[0].population_density=null;rows[1].transit_coverage=null;rows[2].transit_coverage=0;
  await route.fulfill({response,json:rows});
 });
 await page.goto('/');
 const chart=page.locator('.density-transit');
 await expect(chart.locator('.scatter-point')).toHaveCount(48);
 await expect(chart).toContainText('ไม่รวมข้อมูลที่ขาด 2 เขต');
 expect(await chart.locator('.scatter-dot[cx="80"]').count()).toBeGreaterThan(0);
 await page.unroute('**/api/districts');
 await page.route('**/api/districts',async route=>{
  const response=await route.fetch();const rows=await response.json();
  await route.fulfill({response,json:rows.map((r:any)=>({...r,transit_coverage:null}))});
 });
 await page.reload();
 await expect(chart).toContainText('ไม่มีเขตที่มีข้อมูลครบทั้งสองตัวชี้วัดในกลุ่มนี้');
 await expect(chart.locator('.scatter-point')).toHaveCount(0);
});
