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
 await new Promise(resolve=>server.listen(18799,'127.0.0.1',resolve));browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
 await context.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:18799/')?r.continue():r.abort());
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:18799/showroom.html');await page.getByRole('heading',{name:'Your rooms.',exact:true}).waitFor();
 await page.evaluate(()=>{
  const owner={id:'owner',name:'Home owner',username:'owner',owner:true,administrator:true,role:'administrator',active:true,local_only:false,password_supported:true};
  const family={id:'family',name:'Family <member>',username:'family',owner:false,administrator:false,role:'member',active:true,local_only:false,password_supported:true};
  const client=StudioApp.client,original=client.request.bind(client);window.ACCOUNT_CALLS=[];window.TEST_REVIEW=null;
  client.request=async(op,data={})=>{
   if(!op.startsWith('accounts/'))return original(op,data);ACCOUNT_CALLS.push({op,data});
   if(op==='accounts/me')return owner;
   if(op==='accounts/list')return {users:[owner,family]};
   if(op==='accounts/preview'){TEST_REVIEW={...data,user:family};return {approval_nonce:'fixture-review',plan:TEST_REVIEW,writes:false}}
   if(op==='accounts/approve')return {status:'saved'};
   if(op==='accounts/password')return {status:'saved',sign_in_again:true};
   throw Error('Unexpected fixture operation');
  };
 });
 await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.getByRole('button',{name:'Home Care',exact:true}).click();
 await page.getByRole('button',{name:'Household access',exact:true}).click();await page.getByRole('heading',{name:'Family <member>',exact:true}).waitFor();
 assert.equal(await page.locator('member').count(),0);assert.equal(await page.getByRole('button',{name:'Remove access',exact:true}).count(),1,'Owner must not have a remove control');
 await page.getByRole('button',{name:'Add a person',exact:true}).click();await page.getByLabel('Person’s name',{exact:true}).fill('A new person');
 await page.getByLabel('Choose a username',{exact:true}).fill('new_person');await page.getByLabel('Household role',{exact:true}).selectOption('viewer');
 await page.getByRole('button',{name:'Review account',exact:true}).click();await page.getByRole('heading',{name:'Add this person?',exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>ACCOUNT_CALLS.filter(c=>c.op==='accounts/approve').length),0);
 await page.getByLabel('Your current password',{exact:true}).fill('fixture-current-password');await page.getByLabel('New account password',{exact:true}).fill('fixture-new-password');await page.getByLabel('Repeat new account password',{exact:true}).fill('different-password');
 await page.getByRole('button',{name:'Add person',exact:true}).click();await page.getByText('The two new passwords need to match.',{exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>ACCOUNT_CALLS.filter(c=>c.op==='accounts/approve').length),0);
 for(const label of ['Your current password','New account password','Repeat new account password'])assert.equal(await page.getByLabel(label,{exact:true}).inputValue(),'');
 await page.getByLabel('Your current password',{exact:true}).fill('fixture-current-password');await page.getByLabel('New account password',{exact:true}).fill('fixture-new-password');await page.getByLabel('Repeat new account password',{exact:true}).fill('fixture-new-password');
 await page.screenshot({path:path.resolve(__dirname,'../evidence/household-review-phone.png'),fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.getByRole('button',{name:'Add person',exact:true}).click();await page.getByRole('heading',{name:'Household access.',exact:true}).waitFor();
 assert.equal(await page.evaluate(()=>ACCOUNT_CALLS.filter(c=>c.op==='accounts/approve').length),1);
 await page.locator('#close-dialog').click();await page.getByRole('button',{name:'Your account',exact:true}).click();await page.getByRole('button',{name:'Change my password',exact:true}).click();
 await page.getByLabel('Current password',{exact:true}).fill('fixture-secret');await page.locator('#close-dialog').click();assert.equal(await page.getByLabel('Current password',{exact:true}).inputValue(),'','Closing a password dialog must clear its fields');
 await context.close();assert.deepEqual(errors,[]);
 const member=await browser.newContext(),memberPage=await member.newPage();await memberPage.goto('http://127.0.0.1:18799/showroom.html?role=member');await memberPage.getByRole('heading',{name:'Your rooms.',exact:true}).waitFor();
 await memberPage.getByRole('button',{name:'Home Care',exact:true}).click();assert.equal(await memberPage.getByRole('button',{name:'Household access',exact:true}).count(),0);
 await memberPage.getByRole('button',{name:'Your account',exact:true}).click();assert.equal(await memberPage.getByRole('button',{name:'Change my password',exact:true}).count(),1);await member.close();
 fs.writeFileSync(path.resolve(__dirname,'../evidence/household-browser.json'),JSON.stringify({status:'passed',scope:'Inert household API fixture, not real user/password or physical-device acceptance',checks:['owner has no removal control','account labels remain text','review sends no mutation','view-only role can be selected','password mismatch sends no approval','password fields clear after submission and on closing','phone review fits without horizontal overflow','member has no household administration entry but has own password entry','no uncaught browser errors']},null,2));
 console.log('PASS: household review, owner protection, password cleanup, role choices and member/phone views.');
}finally{await browser?.close();if(server)await new Promise(resolve=>server.close(resolve))}})().catch(e=>{console.error(e.name,e.message);process.exitCode=1});
