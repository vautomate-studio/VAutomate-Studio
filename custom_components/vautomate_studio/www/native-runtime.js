/* Injected by the dedicated customer APK into its bundled top-level document. */
(()=>{'use strict';
 if(window.__VA_NATIVE__)return;
 const nonce='__VA_NATIVE_NONCE__',requests=new Map();let port=null,serial=0;
 const call=(method,data={})=>new Promise((resolve,reject)=>{if(!port)return reject(Error('The app connection is not ready.'));const id=String(++serial),timer=setTimeout(()=>{requests.delete(id);reject(Error('The app connection timed out.'))},20000);requests.set(id,{resolve,reject,timer});port.postMessage(JSON.stringify({id,method,data}))});
 function back(){if(document.querySelector('#dialog')?.open){document.querySelector('#close-dialog')?.click();return}if(location.hash&&location.hash!=='#/home'){history.back();return}call('app.exit').catch(()=>{})}
 Object.defineProperty(window,'__VA_NATIVE__',{value:Object.freeze({call,back,forget:()=>window.StudioApp.client.signout()}),writable:false});
 document.body.classList.add('native');
 window.addEventListener('message',async event=>{if(event.data!=='vautomate-native-port-v1|'+nonce||!event.ports?.length||(event.source&&event.source!==window)||(event.origin&&event.origin!==location.origin))return;if(port)port.close();port=event.ports[0];port.onmessage=event=>{let message;try{message=JSON.parse(event.data)}catch{return}const pending=requests.get(message.id);if(!pending)return;clearTimeout(pending.timer);requests.delete(message.id);message.error?pending.reject(Error(message.error)):pending.resolve(message.result)};port.start();call('app.ready').catch(()=>{});await window.restoreRememberedSession()});
})();
