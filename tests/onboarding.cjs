/* First-owner API policy: synthetic responses only, no home or account changes. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../frontend/onboarding.js'),'utf8');
class StudioError extends Error{constructor(code,message){super(message);this.code=code}}
function fixture(options={}){
 const calls=[];let owner=options.existing||false;
 const client={clientId:'http://fixture:8123/',access:'',auth:async(route,body)=>{calls.push({route,body});return {access_token:'fixture-access',refresh_token:'fixture-refresh'}},applySession:s=>{client.access=s.access_token},remember:async()=>calls.push({route:'native-vault'}),open:()=>calls.push({route:'open-websocket'})};
 const context=vm.createContext({window:{},StudioError,location:new URL('http://fixture:8123/vautomate-studio/index.html'),AbortSignal,fetch:async(url,init)=>{
  const route=new URL(url).pathname;calls.push({url,route,init,body:init.body?JSON.parse(init.body):undefined});
  let status=200,body={};
  if(route==='/api/vautomate_studio/v1/health')body={api_version:1,initialized:true};
  else if(route==='/api/onboarding'){if(options.completed)status=404;body=[{step:'user',done:owner},{step:'core_config',done:false},{step:'analytics',done:false},{step:'integration',done:false},...(options.unknown?[{step:'future_required_step',done:false}]:[])]}
  else if(route==='/api/onboarding/users'){owner=true;body={auth_code:'fixture-code'}}
  else if(route==='/api/config/config_entries/flow')body=options.missingPackage?{type:'abort',reason:'invalid_handler'}:options.alreadyConfigured?{type:'abort',reason:'already_configured'}:{type:'form',step_id:'user',data_schema:[],flow_id:options.ulid?'0'.repeat(26):'a'.repeat(32)};
  else if(route.endsWith('/flow/'+(options.ulid?'0'.repeat(26):'a'.repeat(32))))body={type:'create_entry'};
  if(options.forbidden&&route.includes('/config_entries/'))status=403;
  return {ok:status===200,status,json:async()=>body};
 }});vm.runInContext(source,context);return {api:context.window.StudioOnboarding,client,calls};
}
(async()=>{
 let f=fixture();assert((await f.api.probe(f.client)).needsOwner);assert.equal(f.calls.filter(c=>c.init?.method==='POST').length,0,'Detection must not create anything');
 await f.api.create(f.client,{name:'Test owner',username:'test_owner',password:'fixture-password-long'});
 assert.equal(f.calls.filter(c=>c.route==='/api/onboarding/users').length,1);assert.equal(f.calls.at(-1).route,'open-websocket');
 assert(f.calls.filter(c=>c.url).every(c=>new URL(c.url).origin==='http://fixture:8123'));assert(f.calls.filter(c=>c.url).every(c=>!c.url.includes('fixture-password')));
 assert(!f.calls.find(c=>c.route==='/api/onboarding/users').init.headers.Authorization);assert(f.calls.find(c=>c.route==='/api/onboarding/core_config').init.headers.Authorization);
 assert.deepEqual(f.calls.find(c=>c.route==='/api/onboarding/analytics').body,{},'No analytics opt-in is selected');
 f=fixture({existing:true});await assert.rejects(f.api.create(f.client,{name:'Owner',username:'owner',password:'fixture-password-long'}),e=>e.code==='already_configured');assert(!f.calls.some(c=>c.init?.method==='POST'));
 f=fixture();await assert.rejects(f.api.create(f.client,{name:'Owner',username:'owner',password:'short'}),e=>e.code==='invalid_input');assert.equal(f.calls.length,0);for(const password of ['a'.repeat(73),'界'.repeat(25),'😀'.repeat(6)]){await assert.rejects(f.api.create(f.client,{name:'Owner',username:'owner',password}),e=>e.code==='invalid_input');assert.equal(f.calls.length,0)}
 f=fixture({unknown:true,existing:true});f.client.access='fixture';await assert.rejects(f.api.complete(f.client),e=>e.code==='incompatible');assert(!f.calls.some(c=>c.init?.method==='POST'));
 f=fixture({existing:true,missingPackage:true});f.client.access='fixture';await assert.rejects(f.api.complete(f.client),e=>e.code==='installer_required');assert(!f.calls.some(c=>c.route==='open-websocket'));
 f=fixture({existing:true,alreadyConfigured:true});f.client.access='fixture';await f.api.complete(f.client);assert.equal(f.calls.at(-1).route,'open-websocket');
 f=fixture({existing:true,forbidden:true});f.client.access='fixture';await assert.rejects(f.api.complete(f.client),e=>e.code==='not_allowed');
 f=fixture({ulid:true});await f.api.create(f.client,{name:'Owner',username:'owner',password:'fixture-password-long'});assert.equal(f.calls.at(-1).route,'open-websocket');
 f=fixture({completed:true});assert.equal(await f.api.probe(f.client),null);
 console.log('PASS: inert first-owner detection, deliberate creation, same-origin auth, existing-account protection, analytics default, unknown-step guard, safe activation and member rejection.');
})().catch(error=>{console.error(error);process.exitCode=1});
