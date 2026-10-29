/* Inert household UI fixture: no real user or credential changes. */
const {chromium}=require('@playwright/test');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../frontend');let browser,server;
(async()=>{try{
 server=http.createServer((req,res)=>{
  const file=path.resolve(root,new URL(req.url,'http://fixture').pathname.slice(1));
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return}
  res.setHeader('Content-Type',({'.js':'text/javascript','.html':'text/html','.css':'text/css','.svg':'image/svg+xml'})[path.extname(file)]||'text/plain');res.end(fs.readFileSync(file));
 });
 await new Promise(resolve=>server.listen(18801,'127.0.0.1',resolve));browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
 await context.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:18801/')?r.continue():r.abort());
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:18801/showroom.html');await page.getByRole('heading',{name:'Your rooms.',exact:true}).waitFor();
 await page.evaluate(()=>{
  const client=StudioApp.client,original=client.request.bind(client);window.PAIR_CALLS=[];window.PAIR_SESSION=null;window.PAIR_NEW=false;
  client.request=async(op,data={})=>{
   if(!op.startsWith('pairing/'))return original(op,data);PAIR_CALLS.push({op,data});
   if(op==='pairing/status')return {controllers:[{id:'network',name:'Home Zigbee',online:true}],can_start:true,session:PAIR_SESSION?{...PAIR_SESSION,devices:PAIR_NEW?[{id:'new',name:'Pendant <device>',stage:'ready',entities:[{entity_id:'light.new_pendant',name:'Pendant'}]}]:[]}:null};
   if(op==='pairing/preview')return {approval_nonce:'review',plan:{...data,room_name:'Living room',controller_name:'Home Zigbee',duration:60}};
   if(op==='pairing/begin'){PAIR_SESSION={id:'session',phase:'listening',room_id:'living',seconds_remaining:60};return {status:'listening'}}
   if(op==='pairing/cancel'){PAIR_SESSION.phase='closed';return {status:'closed'}}
   if(op==='pairing/assign'){const home=StudioApp.state.home,layout=structuredClone(home.layout);layout.rooms.find(r=>r.id===data.room_id).entities.push(...data.entities);return {revision:home.revision+1,layout,assigned:true,device_operated:false}}
   throw Error('Unexpected fixture operation');
  };
 });
 await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.getByRole('button',{name:'Home Care',exact:true}).click();await page.getByRole('button',{name:'Add a device',exact:true}).click();
 await page.getByRole('button',{name:'Review pairing',exact:true}).click();await page.getByRole('heading',{name:'Ready to connect?',exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>PAIR_CALLS.filter(c=>c.op==='pairing/begin').length),0);assert(await page.getByRole('button',{name:'Start pairing',exact:true}).isDisabled());
 await page.getByLabel('My device is ready to pair',{exact:true}).check();await page.getByRole('button',{name:'Start pairing',exact:true}).click();await page.getByRole('button',{name:'Stop pairing',exact:true}).waitFor();
 await page.evaluate(()=>{PAIR_NEW=true});await page.getByRole('heading',{name:'Pendant <device>',exact:true}).waitFor();assert.equal(await page.locator('device').count(),0);
 const stop=page.getByRole('button',{name:'Stop pairing',exact:true});await stop.focus();await page.waitForTimeout(2800);assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Stop pairing','Polling must preserve remote focus');
 await page.getByRole('button',{name:'Add to room',exact:true}).click();await page.getByText('Device controls added to Living room.').waitFor();
 assert.equal(await page.evaluate(()=>PAIR_CALLS.filter(c=>c.op==='pairing/assign').length),1);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.screenshot({path:path.resolve(__dirname,'../evidence/pairing-phone.png'),fullPage:true});await stop.click();await page.getByRole('button',{name:'Add another device',exact:true}).click();await page.getByRole('button',{name:'Review pairing',exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>PAIR_CALLS.filter(c=>c.op==='pairing/begin').length),1);
 await context.close();assert.deepEqual(errors,[]);
 const member=await browser.newContext(),memberPage=await member.newPage();await memberPage.goto('http://127.0.0.1:18801/showroom.html?role=member');await memberPage.getByRole('heading',{name:'Your rooms.',exact:true}).waitFor();await memberPage.getByRole('button',{name:'Home Care',exact:true}).click();assert.equal(await memberPage.getByRole('button',{name:'Add a device',exact:true}).count(),0);await member.close();
 fs.writeFileSync(path.resolve(__dirname,'../evidence/pairing-browser.json'),JSON.stringify({status:'passed',scope:'Inert pairing fixture only; no physical radio acceptance',checks:['inert review','readiness required','poll preserves focus','device names are text','explicit room assignment','explicit close','next review never reopens','phone fits','member isolated','no browser errors']},null,2));
 console.log('PASS: reviewed pairing, stable focus, room placement, closure and member isolation.');
}finally{await browser?.close();if(server)await new Promise(resolve=>server.close(resolve))}})().catch(e=>{console.error(e.name,e.message);process.exitCode=1});
