/* Refresh/reopen regression tests; synthetic credentials, no home traffic. */
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../frontend/client.js'),'utf8');
const store=()=>{const values=new Map();return {getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)}};
function page(local=store(),session=store(),options={}){
 const calls=[],timers=new Map();let serial=0,logins=0,opens=0;
 const window={localStorage:local,sessionStorage:session,...options.window};
 const context=vm.createContext({window,location:new URL(options.origin||'http://home:8123/vautomate-studio/index.html'),URL,URLSearchParams,AbortSignal,setTimeout:(fn,ms)=>{timers.set(++serial,{fn,ms});return serial},clearTimeout:id=>timers.delete(id),fetch:async(url,input)=>{calls.push(new URLSearchParams(input.body));if(options.offline)throw Error('Network down');return options.invalid?{ok:false,status:400}:{ok:true,status:200,json:async()=>({access_token:'test-access',refresh_token:'test-refresh',expires_in:1800})}}});
 vm.runInContext(source,context);const c=new window.StudioClient();c.open=()=>opens++;c.onlogin=()=>logins++;
 return {c,calls,timers,local,session,get logins(){return logins},get opens(){return opens}};
}
(async()=>{
 let p=page();await p.c.finish('code');const saved=JSON.parse(p.local.getItem(p.c.sessionKey));assert.equal(saved.credential,'test-refresh');assert(!JSON.stringify(saved).includes('test-access'));assert(!JSON.stringify(saved).includes('code'));
 let reload=page(p.local,p.session);await reload.c.restore();assert.equal(reload.logins,0);assert.equal(reload.opens,1);assert.equal(reload.calls[0].get('grant_type'),'refresh_token');
 let reopened=page(p.local);await reopened.c.restore();assert.equal(reopened.opens,1,'Remembered sign-in survives a new tab');
 await reopened.c.signout();assert.equal(reopened.local.getItem(reopened.c.sessionKey),null);assert.equal(reopened.session.getItem(reopened.c.sessionKey),null);assert.equal(reopened.calls.at(-1).get('action'),'revoke');
 p=page();p.c.rememberDevice=false;await p.c.finish('code');assert.equal(p.local.getItem(p.c.sessionKey),null);reload=page(p.local,p.session);await reload.c.restore();assert.equal(reload.opens,1);assert.equal(reload.c.rememberDevice,false);reopened=page(p.local);await reopened.c.restore();assert.equal(reopened.logins,1,'Shared-device session ends with its tab');
 p=page();await p.c.finish('code');const invalid=page(p.local,p.session,{invalid:true});await invalid.c.restore();assert.equal(invalid.logins,1);assert.equal(p.local.getItem(p.c.sessionKey),null,'Revoked token is forgotten');
 p=page();await p.c.finish('code');const offline=page(p.local,p.session,{offline:true});await offline.c.restore();assert.equal(offline.logins,0);assert(offline.local.getItem(offline.c.sessionKey));assert([...offline.timers.values()].some(t=>t.ms===10000),'Outage retries without asking for credentials');
 const foreign=page(p.local,p.session,{origin:'http://other-home:8123'});await foreign.c.restore();assert.equal(foreign.logins,1);assert.equal(foreign.calls.length,0,'Never sends a browser credential to another origin');
 let vault;const native=page(store(),store(),{window:{__VA_NATIVE__:{call:async(method,value)=>{if(method==='session.save')vault=value;if(method==='session.read')return vault}}}});await native.c.finish('code');assert.equal(native.local.getItem(native.c.sessionKey),null);assert.equal(native.session.getItem(native.c.sessionKey),null);const remote=page(store(),store(),{origin:'http://remote-home:8123',window:{__VA_NATIVE__:{call:async(method)=>method==='session.read'?vault:null}}});await remote.c.restore();assert.equal(remote.opens,1);assert.equal(remote.calls[0].get('client_id'),'http://home:8123/','Native home vault preserves the original OAuth client across local/remote');
 console.log('PASS: remembered refresh/reopen, tab-only sessions, revocation, logout, outage retention, origin isolation and native vault restoration.');
})().catch(e=>{console.error(e);process.exitCode=1});
