// Report elements wider than the page content box (print layout)
const { chromium } = require('playwright'); const path=require('path');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:680,height:1000}});
await p.emulateMedia({media:'print'});
await p.goto('file://'+path.resolve(__dirname,'../out/pathology.html'),{waitUntil:'networkidle'});
await p.evaluate(()=>document.fonts.ready);
const r=await p.evaluate(()=>{const W=document.body.clientWidth;const out=[];
 document.querySelectorAll('table,.figs,.tree,.flow,.hflow,.cols,pre').forEach(e=>{if(e.scrollWidth>e.clientWidth+2||e.getBoundingClientRect().right>W+4){let h=e.previousElementSibling;while(h&&!/^H[1-4]$/.test(h.tagName))h=h.previousElementSibling;out.push(e.tagName+'.'+e.className+' w='+e.scrollWidth+' cw='+e.clientWidth+' after: '+(h?h.textContent.slice(0,50):''))}});return [W,out]});
console.log(JSON.stringify(r,null,1));await b.close()})();
