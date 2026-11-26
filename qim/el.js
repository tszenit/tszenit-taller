const {chromium}=require('playwright');
(async()=>{const [f,pref,tab,...sels]=process.argv.slice(2);const b=await chromium.launch();const p=await b.newPage({viewport:{width:1000,height:900}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+f);await p.waitForTimeout(400);
if(tab!=='-'){await p.click('.tile[data-tab="'+tab+'"]');await p.waitForTimeout(300);}
await p.evaluate(()=>document.querySelectorAll('details').forEach(d=>d.open=true));
let i=0;for(const s of sels){const el=p.locator(s).first();await el.scrollIntoViewIfNeeded();await el.screenshot({path:pref+(i++)+'.png'});}
console.log('errors:',JSON.stringify(errs));await b.close();})();
