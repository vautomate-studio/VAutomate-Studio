/* Deterministic outage tests: no real server, delays or device commands. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
let now=0,next=0,sockets=[],timers=new Map(),frames=[];
const schedule=(fn,ms)=>{const id=++next;timers.set(id,{at:now+ms,fn});return id};
function advance(ms){const end=now+ms;for(;;){const entry=[...timers].filter(([,v])=>v.at<=end).sort((a,b)=>a[1].at-b[1].at)[0];if(!entry)break;timers.delete(entry[0]);now=entry[1].at;entry[1].fn()}now=end}
class Socket{
 constructor(){this.readyState=1;sockets.push(this)}
 send(raw){frames.push(JSON.parse(raw))}
 close(){this.readyState=3}
 message(value){this.onmessage?.({data:JSON.stringify(value)})}
}
const context=vm.createContext({window:{},location:new URL('http://lab:8123/vautomate-studio/index.html'),WebSocket:Socket,URL,URLSearchParams,AbortSignal,crypto:require('node:crypto').webcrypto,Math:Object.assign(Object.create(Math),{random:()=>0}),setTimeout:schedule,clearTimeout:id=>timers.delete(id)});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../frontend/client.js'),'utf8'),context);
function client(){timers.clear();frames=[];sockets=[];const c=new context.window.StudioClient();c.access='fixture';return c}
function authenticate(s){s.message({type:'auth_required'});s.message({type:'auth_ok'})}
(async()=>{
 let c=client();c.open();const abandoned=sockets[0],staleMessage=abandoned.onmessage;advance(15000);assert.equal(abandoned.readyState,3,'Handshake deadline closes a stalled socket');assert.equal(c.connected,false);advance(1500);assert.equal(sockets.length,2);staleMessage({data:JSON.stringify({type:'auth_ok'})});assert.equal(c.connected,false,'Old sockets cannot change connection state');authenticate(sockets[1]);assert(c.connected);await c.signout();assert.equal(timers.size,0);

 c=client();c.open();authenticate(sockets[0]);advance(20000);const ping=frames.at(-1);assert.equal(ping.type,'ping');sockets[0].message({type:'pong',id:ping.id+1});advance(10000);assert.equal(c.connected,false,'Unmatched pong cannot keep a dead connection alive');advance(1500);assert.equal(sockets.length,2);authenticate(sockets[1]);advance(20000);sockets[1].message({type:'pong',id:frames.at(-1).id});advance(10000);assert(c.connected,'Matching heartbeat keeps the connection healthy');await c.signout();assert.equal(timers.size,0);

 c=client();c.open();authenticate(sockets[0]);const result=assert.rejects(c.command({entity_id:'light.fixture',action:'turn_on'}),e=>e.code==='connection_lost');const actions=()=>frames.filter(f=>f.operation==='command').length;assert.equal(actions(),1);const staleClose=sockets[0].onclose;sockets[0].onerror();await result;c.open();authenticate(sockets.at(-1));staleClose();advance(5000);assert.equal(sockets.length,2,'Manual recovery cancels an older reconnect timer');assert.equal(actions(),1,'An uncertain device command is never replayed');assert(c.connected);await c.signout();assert.equal(timers.size,0);advance(60000);assert.equal(sockets.length,2,'Sign-out cancels every reconnect and watchdog');
 console.log('PASS: handshake deadlines, heartbeat recovery, stale callbacks, retry cancellation, no command replay and sign-out cleanup.');
})().catch(error=>{console.error(error);process.exitCode=1});
