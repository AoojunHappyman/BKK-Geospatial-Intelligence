import {chromium} from '@playwright/test';
const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:390,height:844}});
page.on('console',m=>console.log(m.type(),m.text()));page.on('pageerror',e=>console.log('PAGEERROR',e.message));
await page.goto('http://127.0.0.1:5173/');await page.waitForTimeout(6000);
console.log(await page.evaluate(()=>({canvases:[...document.querySelectorAll('canvas')].map(c=>({w:c.width,h:c.height})),text:document.querySelector('.map-error')?.textContent})));
await page.locator('.map[data-rendered-districts="50"]').waitFor();
await page.waitForTimeout(1500);
await page.screenshot({path:'docs/screenshots/mobile.png',fullPage:true});
await browser.close();
