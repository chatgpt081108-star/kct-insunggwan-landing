const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const [,,total,test]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.addInitScript(pl=>{window.PLAN=pl},JSON.parse(fs.readFileSync('plan.json')));
await p.goto('file://'+process.cwd()+'/overlay.html');await p.evaluate(()=>window.ready);
fs.rmSync('ov',{recursive:true,force:true});fs.mkdirSync('ov');
const times=test?test.split(',').map(Number):[...Array(Math.round(total*30)).keys()].map(f=>f/30);
for(let i=0;i<times.length;i++){await p.evaluate(t=>window.seek(t),times[i]);await p.screenshot({path:`ov/o${String(i).padStart(5,'0')}.png`,omitBackground:true});}
await b.close()})()
