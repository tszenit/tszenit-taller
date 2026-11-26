const {chromium}=require('playwright');
(async()=>{const [f,pref]=process.argv.slice(2);const b=await chromium.launch();const p=await b.newPage({viewport:{width:1000,height:900}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+f);await p.waitForTimeout(400);
const tabs=await p.$$eval('.tile',ts=>ts.map(t=>t.dataset.tab));let i=0;
for(const t of tabs){await p.click('.tile[data-tab="'+t+'"]');await p.waitForTimeout(200);
 const n=await p.locator('#'+t+' .tool').count();
 for(let j=0;j<n;j++){const el=p.locator('#'+t+' .tool').nth(j);await el.scrollIntoViewIfNeeded();await p.evaluate(()=>{const b=document.querySelector('.bar');if(b)b.style.visibility='hidden'});await el.screenshot({path:pref+(i++)+'.png'});await p.evaluate(()=>{const b=document.querySelector('.bar');if(b)b.style.visibility=''});}}
console.log(i,'tools; errors:',JSON.stringify(errs));await b.close();})();
