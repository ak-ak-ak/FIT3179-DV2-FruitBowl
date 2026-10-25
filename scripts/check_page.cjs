// BROWSER TEST ONLY: Playwright controls a separate headless browser, not the published page.
// Environment variables let the same checks target local preview or the public deployment.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/Users/ak/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({headless:true, executablePath:process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const errors = [];
  const dataFiles = new Set();
  // Test small-laptop, desktop and mobile viewports with a fresh page for each.
  for (const [width,height] of [[1366,768],[1280,800],[390,844]]) {
    const page = await browser.newPage({viewport:{width,height}});
    page.on('pageerror',e => errors.push(e.message));
    page.on('console',m => { if(m.type()==='error') errors.push(m.text()); });
    // Record unique chart-data URLs so repeated requests do not inflate the download budget.
    page.on('response',r => {
      const pathname = new URL(r.url()).pathname;
      const relative = pathname.includes('/data/') ? 'data/'+pathname.split('/data/')[1] : null;
      if(relative) dataFiles.add(relative);
    });
    await page.goto(process.env.DV2_URL || 'http://127.0.0.1:8765/',{waitUntil:'networkidle'});
    await page.evaluate(() => document.fonts.ready);
    await page.addStyleTag({content:'html { scroll-behavior: auto !important; }'});
    if(await page.locator('.chart svg').count() !== 11) throw Error('Eleven charts did not render');
    if(await page.locator('#fruit_value .mark-symbol.role-mark path').count()!==10) throw Error('Expected ten value dots');
    const missingDots=await page.locator('#fruit_value .mark-symbol.role-mark path').evaluateAll(es=>es.filter(e=>!e.getAttribute('fill') || e.getAttribute('fill')==='none').length);
    if(missingDots) throw Error('Value dots missing colours');
    if(await page.locator('#fruit_heatmap .mark-text.role-mark text').count()) throw Error('Heatmap should not have per-cell text');
    if(await page.locator('#regional_leaders li').count()!==4) throw Error('Regional context not populated');
    if(width>=1100) {
      const tops=await page.locator('.overview .chart svg').evaluateAll(es=>es.map(e=>e.getBoundingClientRect().top));
      if(Math.abs(tops[0]-tops[1])>1) throw Error('Overview chart tops are misaligned');
    }
    const whitePanels=await page.locator('.chart').evaluateAll(es=>es.filter(e=>getComputedStyle(e).backgroundColor==='rgb(255, 255, 255)').length);
    if(whitePanels) throw Error('White chart panels should be transparent');
    const bumpGap=await page.locator('#fruit_bump svg').evaluate(svg=>{
      const years=[...svg.querySelectorAll('.role-axis-label text')].filter(e=>/^202\d-\d\d$/.test(e.textContent));
      const dots=[...svg.querySelectorAll('.mark-symbol.role-mark path')];
      return Math.min(...years.map(e=>e.getBoundingClientRect().top))-Math.max(...dots.map(e=>e.getBoundingClientRect().bottom));
    });
    if(bumpGap<8) throw Error('Bump chart marks are too close to year labels');
    // SVG mark counts catch charts that render a container but omit expected observations.
    for(const [selector,count] of [['#fruit_units .mark-rect.role-mark path',100],['#fruit_sankey .productionLinks path',56],['#fruit_sankey .productionNodes path',17],['#fruit_waterfall .mark-rect.role-mark path',9]]) {
      if(await page.locator(selector).count()!==count) throw Error('Unexpected mark count '+selector);
    }
    const checkOverflow = async () => {
      if(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) {
        console.log(await page.locator('.chart').evaluateAll(es=>es.map(e=>({id:e.id,width:e.getBoundingClientRect().width,svg:e.querySelector('svg')?.getBoundingClientRect().width}))),await page.viewportSize());
        throw Error('Horizontal overflow at '+width);
      }
    };
    await checkOverflow();
    // Exercise every dropdown option, then check targeted labels for intersecting rectangles.
    for (const select of await page.locator('.chart select').all()) {
      const initialValue = await select.inputValue();
      const options = await select.locator('option').evaluateAll(es => es.map(e => e.value));
      for (const option of options) {
        await select.selectOption(option, {force:true});
        await page.waitForTimeout(50);
        await checkOverflow();
        const id = await select.evaluate(e => e.closest('.chart').id);
        if(id==='fruit_exports') {
          const keys=await page.locator('#export_destinations .route-key').evaluateAll(es=>es.map(e=>getComputedStyle(e).backgroundColor));
          const routes=await page.locator('#fruit_exports .exportRoutes path').evaluateAll(es=>es.map(e=>getComputedStyle(e).stroke));
          if(new Set(keys).size!==8 || JSON.stringify(keys)!==JSON.stringify(routes)) throw Error('Destination colours do not match routes');
        }
        if(id==='fruit_trajectory') {
          const text=await page.locator('#trajectory_insight').textContent();
          if(!text.startsWith(option+':') || /NaN|undefined/.test(text)) throw Error('Trajectory insight not synchronised');
        }
        if(['fruit_exports','fruit_trajectory','fruit_sankey'].includes(id)) {
          const collisions = await page.locator('#'+id+' .mark-text.role-mark text').evaluateAll(es => {
            const boxes=es.filter(e=>e.textContent && getComputedStyle(e).opacity!=='0').map(e=>({text:e.textContent,b:e.getBoundingClientRect()}));
            return boxes.flatMap((a,i)=>boxes.slice(i+1).filter(c=>a.b.left<c.b.right && a.b.right>c.b.left && a.b.top<c.b.bottom && a.b.bottom>c.b.top).map(c=>[a.text,c.text]));
          });
          if(collisions.length) throw Error(id+' label collisions '+option+' '+JSON.stringify(collisions));
        }
      }
      await select.selectOption(initialValue, {force:true});
      await select.focus();
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Tab');
      await select.selectOption(initialValue, {force:true});
    }
    for(const selector of ['#fruit_units .mark-rect.role-mark path','#fruit_sankey .productionLinks path','#fruit_waterfall .mark-rect.role-mark path']) {
      await page.locator(selector).first().hover({force:true});
      await page.waitForTimeout(80);
      if(!await page.locator('#vg-tooltip-element').isVisible()) throw Error('Tooltip unavailable '+selector);
      await page.mouse.move(0,0);
    }
    // Check assets/fonts and narrative section membership as well as chart interactions.
    const assets = await page.locator('img').evaluateAll(es => es.filter(e => !e.complete || !e.naturalWidth).map(e=>e.src));
    if(assets.length) throw Error('Broken images '+assets.join(','));
    const fonts = await page.evaluate(() => document.fonts.check('600 20px Fraunces') && document.fonts.check('17px "Nunito Sans"'));
    if(!fonts) throw Error('Fonts not ready');
    const sections = await page.locator('main section').evaluateAll(es => es.map(e => e.querySelectorAll('.chart').length));
    if(JSON.stringify(sections)!=='[2,4,4,1]') throw Error('Incorrect section order '+sections);
    const clippedLabels = await page.locator('#fruit_sankey svg').evaluate(svg => {
      const b=svg.getBoundingClientRect();
      return [...svg.querySelectorAll('text')].filter(t=>{
        const r=t.getBoundingClientRect();
        return r.top<b.top || r.bottom>b.bottom || r.left<b.left || r.right>b.right;
      }).map(t=>t.textContent);
    });
    if(clippedLabels.length) throw Error('Clipped Sankey labels '+clippedLabels.join(','));
    // These screenshots are local QA outputs; this test never commits or deploys anything.
    await page.screenshot({path:path.join('/private/tmp',`dv2-final-${width}.png`),fullPage:true});
    for(const id of ['fruit_units','fruit_sankey','fruit_waterfall','fruit_exports']) {
      await page.locator('#'+id).screenshot({path:path.join('/private/tmp',`dv2-${id}-${width}.png`)});
    }
    // Resize the already-rendered page to test ResizeObserver, not just initial page loading.
    await page.setViewportSize({width:width===390?1280:390,height:800});
    await page.waitForTimeout(400);
    await checkOverflow();
    console.log('PASS',width,height,'11 charts, selectors, assets, fonts, resize');
    await page.close();
  }
  await browser.close();
  const dataBytes = [...dataFiles].reduce((sum,file)=>sum+fs.statSync(path.resolve(__dirname,'..',file)).size,0);
  const assets = path.resolve(__dirname,'../assets');
  const artBytes = fs.statSync(path.join(assets,'fruit-bowl.webp')).size + fs.readdirSync(path.join(assets,'icons')).reduce((sum,file)=>sum+fs.statSync(path.join(assets,'icons',file)).size,0);
  if(dataBytes>=1000000 || artBytes>=500000) throw Error('Asset budget exceeded');
  console.log('Unique chart data bytes:',dataBytes,'Illustration bytes:',artBytes);
  if(errors.length) throw Error(errors.join('\n'));
})().catch(e => { console.error(e); process.exit(1); });
