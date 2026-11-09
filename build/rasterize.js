// Render img/gen/*.svg to img/gen-png/*.png (2x) with the handwriting font, for <img> use in the HTML apps.
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{const root=path.resolve(__dirname,'..');const src=path.join(root,'img/gen');const dst=path.join(root,'img/gen-png');fs.mkdirSync(dst,{recursive:true});
const b=await chromium.launch();const p=await b.newPage({deviceScaleFactor:2,viewport:{width:760,height:600}});
for(const f of fs.readdirSync(src).filter(f=>f.endsWith('.svg'))){
 const svg=fs.readFileSync(path.join(src,f),'utf8');
 await p.setContent(`<html><head><link href="https://fonts.googleapis.com/css2?family=Coming+Soon&display=block" rel="stylesheet"><style>body{margin:0;background:#FFFEF2}div{width:740px;padding:10px}svg{width:100%;height:auto;display:block}</style></head><body><div id="d">${svg}</div></body></html>`,{waitUntil:'networkidle'});
 await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(200);
 await (await p.$('#d')).screenshot({path:path.join(dst,f.replace('.svg','.png'))});console.log('png',f)}
await b.close()})();
