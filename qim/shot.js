const {chromium}=require('playwright');
(async()=>{const [f,out,tab,w,h,full]=process.argv.slice(2);const b=await chromium.launch();const p=await b.newPage({viewport:{width:+w||1100,height:+h||900}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
await p.goto('file://'+f);await p.waitForTimeout(500);
if(tab&&tab!=='-'){await p.click('.tile[data-tab="'+tab+'"]');await p.waitForTimeout(300);}
await p.screenshot({path:out,fullPage:full==='1'});console.log('errors:',JSON.stringify(errs));await b.close();})();
