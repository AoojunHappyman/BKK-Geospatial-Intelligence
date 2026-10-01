import {test,expect} from '@playwright/test';

test('selection, comparison and share survive navigation, reload and browser back',async({page,context})=>{
 await page.goto('/districts?metric=transit_coverage&q=ปทุมวัน&district=1007');
 const panel=page.getByRole('complementary',{name:'รายละเอียดเขตที่เลือก'});
 await expect(panel.getByRole('heading',{name:'ปทุมวัน'})).toBeVisible();
 await panel.getByRole('button',{name:'เพิ่มเพื่อเปรียบเทียบ',exact:true}).click();
 await page.getByRole('link',{name:'ดูโปรไฟล์เต็ม'}).click();
 await page.locator('nav').getByRole('link',{name:'สำรวจรายเขต'}).click();
 await expect(page.getByLabel('ค้นหาเขต',{exact:true})).toHaveValue('ปทุมวัน');
 await expect(page.getByLabel('ตัวชี้วัด',{exact:true})).toHaveValue('transit_coverage');
 await page.getByRole('button',{name:'ปิดรายละเอียดเขต'}).click();
 await page.getByLabel('เลือกเขตบนแผนที่').selectOption('1030');
 await panel.getByRole('button',{name:'เพิ่มเพื่อเปรียบเทียบ',exact:true}).click();
 const sharedUrl=page.url();
 await context.grantPermissions(['clipboard-read','clipboard-write']);
 await page.getByRole('button',{name:'แชร์มุมมองนี้'}).click();
 await expect(page.getByRole('status')).toHaveText('คัดลอกลิงก์แล้ว');
 expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe(sharedUrl);
 const copy=await context.newPage();await copy.goto(sharedUrl);
 await expect(copy.getByRole('complementary',{name:'รายละเอียดเขตที่เลือก'})).toContainText('จตุจักร');
 await expect(copy.locator('.tray-chips button')).toHaveCount(2);await copy.close();
 await page.getByRole('link',{name:'ดูการเปรียบเทียบ'}).click();
 await expect(page.locator('.comparison-grid .panel')).toHaveCount(5);
 await page.reload();await expect(page.locator('.selected-chips button')).toHaveCount(2);
 await page.goBack();await expect(panel).toContainText('จตุจักร');
 await expect(page.getByLabel('ค้นหาเขต',{exact:true})).toHaveValue('ปทุมวัน');
});

test('invalid shared IDs are ignored and selection is capped at four',async({page})=>{
 await page.goto('/compare?districts=1001,1001,9999,1002,1003,1004,1005');
 await expect(page.locator('.selected-chips button')).toHaveCount(4);
 await expect(page.locator('.comparison-grid .panel')).toHaveCount(5);
 await page.getByRole('button',{name:'ล้างทั้งหมด'}).click();
 await expect(page.getByRole('region',{name:'เขตที่เลือกเปรียบเทียบ'})).toHaveCount(0);
 await expect(page.getByText('เริ่มจากสองเขตที่คุณสนใจ')).toBeVisible();
});

test('mobile selection panel and tray fit viewport; clipboard fallback works',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('denied'))}}));
 await page.goto('/districts?district=1007&districts=1007,1030');
 await expect(page.getByRole('complementary',{name:'รายละเอียดเขตที่เลือก'})).toContainText('ปทุมวัน');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.getByRole('button',{name:'แชร์มุมมองนี้'}).click();
 await expect(page.getByLabel('ลิงก์สำหรับแชร์')).toHaveValue(page.url());
 await page.getByRole('button',{name:'นำปทุมวันออกจากชุดเปรียบเทียบ'}).click();
 await expect(page.getByRole('button',{name:'ดูการเปรียบเทียบ',exact:true})).toBeDisabled();
});
