import {test,expect} from '@playwright/test';

test('river and labels render, tooltip follows cursor, reset fits all districts',async({page})=>{
 await page.goto('/');
 const map=page.locator('.map');
 await expect(map).toHaveAttribute('data-rendered-districts','50');
 await expect.poll(async()=>Number(await map.getAttribute('data-rendered-labels'))).toBeGreaterThan(0);
 await expect.poll(async()=>Number(await map.getAttribute('data-rendered-river'))).toBeGreaterThan(0);
 const bounds=(await map.boundingBox())!;
 await page.mouse.move(bounds.x+bounds.width*.5,bounds.y+bounds.height*.5);
 const tooltip=page.getByRole('tooltip');await expect(tooltip).toContainText('ค่าเฉลี่ยรายเขต');
 await expect(tooltip).toContainText('ไม่ถ่วงน้ำหนัก');
 const first=(await tooltip.boundingBox())!;
 await page.mouse.move(bounds.x+bounds.width*.5+10,bounds.y+bounds.height*.5);
 await expect.poll(async()=>(await tooltip.boundingBox())!.x).not.toBe(first.x);
 await page.keyboard.press('Escape');await expect(tooltip).toHaveCount(0);
 const zoom=Number(await map.getAttribute('data-zoom'));
 await page.locator('.maplibregl-ctrl-zoom-in').click();
 await expect.poll(async()=>Number(await map.getAttribute('data-zoom'))).toBeGreaterThan(zoom+.5);
 await page.getByRole('button',{name:'ดูครบ 50 เขต',exact:true}).click();
 await expect(map).toHaveAttribute('data-rendered-districts','50');
 await expect.poll(async()=>Math.abs(Number(await map.getAttribute('data-zoom'))-zoom)).toBeLessThan(.15);
});

test('secondary text meets minimum size and AA contrast on overview',async({page})=>{
 await page.goto('/');await expect(page.getByText('5,422,568',{exact:true})).toBeVisible();
 const failures=await page.locator('.muted,.stat small,.source-note p,.eyebrow,.page-footer,.nav-label,.sidebar-foot small').evaluateAll(elements=>{
  const rgb=(s:string)=>s.match(/[\d.]+/g)!.slice(0,3).map(Number);
  const lum=(c:number[])=>c.map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);
  return elements.flatMap(el=>{const style=getComputedStyle(el);if(!el.getClientRects().length)return [];
   let parent:Element|null=el,bg='rgb(247, 248, 243)';while(parent){const value=getComputedStyle(parent).backgroundColor;if(value!=='rgba(0, 0, 0, 0)'&&value!=='transparent'){bg=value;break;}parent=parent.parentElement;}
   const a=lum(rgb(style.color)),b=lum(rgb(bg)),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
   return ratio<4.5||parseFloat(style.fontSize)<11?[{text:el.textContent?.slice(0,40),ratio,size:style.fontSize}]:[];
  });
 });
 expect(failures).toEqual([]);
});

test('loading skeleton reserves map area and respects reduced motion',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 let release!:()=>void;const gate=new Promise<void>(r=>{release=r;});
 await page.route('**/api/districts',async route=>{await gate;await route.continue();});
 await page.goto('/districts');
 await expect(page.getByRole('status')).toContainText('กำลังโหลดข้อมูล');
 expect((await page.locator('.skeleton-map').first().boundingBox())!.height).toBeGreaterThanOrEqual(480);
 await expect(page.locator('.skeleton').first()).toHaveCSS('animation-name','none');
 await page.screenshot({path:'../docs/screenshots/loading-skeleton.png'});
 release();await expect(page.getByRole('heading',{name:'ทุกเขตมีเรื่องราว'})).toBeVisible();
 await expect(page.locator('.loading-layout')).toHaveCount(0);
});
