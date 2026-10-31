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
 await new Promise(resolve=>server.listen(18802,'127.0.0.1',resolve));browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
 await context.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:18802/')?r.continue():r.abort());
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:18802/showroom.html');await page.getByRole('heading',{name:'Your rooms.',exact:true}).waitFor();
 await page.evaluate(()=>{
 const client=StudioApp.client,original=client.request.bind(client);window.REPLACE_CALLS=[];
 client.request=async(op,data={})=>{
  if(op==='replacements/status')return {entities:[{entity_id:'light.living',name:'Living pendant',missing:true}],scope:'VAutomate references only. External rules are not changed.'};
  if(op==='discover')return {entities:[{entity_id:'light.new',state:'off',attributes:{friendly_name:'New pendant <device>'}}]};
  if(op.startsWith('replacements/')){REPLACE_CALLS.push({op,data});if(op==='replacements/preview')return {approval_nonce:'inert',missing_original:true,changes:{rooms:[{id:'living',name:'Living room'}],home_buttons:[],schedules:[{id:'schedule',name:'Evening'}],automations:[{id:'occupancy',name:'Room presence'}]}};if(op==='replacements/approve')return {status:'saved',affected_rules_stay_paused:true};throw Error('Unexpected replacement operation')}
  return original(op,data);
 };
 });
 await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.getByRole('button',{name:'Home Care',exact:true}).click();await page.getByRole('button',{name:'Replace a device',exact:true}).click();
 assert(await page.getByRole('button',{name:'Review replacement',exact:true}).isDisabled());await page.getByLabel('Old control',{exact:true}).selectOption('light.living');await page.getByLabel('New control',{exact:true}).selectOption('light.new');await page.getByRole('button',{name:'Review replacement',exact:true}).click();await page.getByRole('heading',{name:'Review the replacement.',exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>REPLACE_CALLS.filter(c=>c.op==='replacements/approve').length),0);const approve=page.getByRole('button',{name:'Replace and pause affected rules',exact:true});assert(await approve.isDisabled());await page.getByLabel('I checked that this replacement is suitable',{exact:true}).check();assert(await approve.isDisabled());await page.getByLabel('I will review external scenes and automations separately',{exact:true}).check();assert(await approve.isEnabled());
 assert.equal(await page.locator('device').count(),0);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.resolve(__dirname,'../evidence/replacement-phone.png'),fullPage:true});await approve.click();await page.getByRole('heading',{name:'Replacement saved.',exact:true}).waitFor();assert.equal(await page.evaluate(()=>REPLACE_CALLS.filter(c=>c.op==='replacements/approve').length),1);await context.close();assert.deepEqual(errors,[]);
 const member=await browser.newContext(),memberPage=await member.newPage();await memberPage.goto('http://127.0.0.1:18802/showroom.html?role=member');await memberPage.getByRole('heading',{name:'Your rooms.',exact:true}).waitFor();await memberPage.getByRole('button',{name:'Home Care',exact:true}).click();assert.equal(await memberPage.getByRole('button',{name:'Replace a device',exact:true}).count(),0);await member.close();
 fs.writeFileSync(path.resolve(__dirname,'../evidence/replacement-browser.json'),JSON.stringify({status:'passed',scope:'Inert replacement UI fixture; no physical device acceptance',checks:['explicit old/new selections','review is inert','affected rules and external scope shown','both acknowledgements required','single approval','phone fits','member has no replacement menu','no browser errors']},null,2));console.log('PASS: reviewed replacement, paused-rule notice, explicit consent and member isolation.');
}finally{await browser?.close();if(server)await new Promise(resolve=>server.close(resolve))}})().catch(e=>{console.error(e.name,e.message);process.exitCode=1});
