"""Synchronize the shared interaction standard without adding new runtime asset routes."""
from pathlib import Path

project=Path(__file__).resolve().parents[1]
workspace=project.parents[1]
marker='/* VA_SHARED_UI_STATES_BEGIN */'
css_marker='/* VA_SHARED_UI_STATES_CSS_BEGIN */'
common=(project/'shared/suncalc.js').read_text(encoding='utf-8')+'\n'+(project/'shared/weather.js').read_text(encoding='utf-8')+'\n'+(project/'shared/ui-states.js').read_text(encoding='utf-8')
css=(project/'shared/ui-states.css').read_text(encoding='utf-8').rstrip()
studio=r'''
(()=>{const ui=window.VAutomateUI;
ui.init({scope:()=>state.home?.user?.id?'studio:'+location.origin+':'+(window.__VA_HOME_PROFILE__||'')+':'+state.home.user.id:'',connected:()=>client.connected,hasSession:()=>!!(state.home||client.access||client.refreshToken),checkStatus:async context=>{ui.captureDrafts();if(!client.connected){if(client.refreshToken)return client.refresh();return connection()}document.querySelector('#dialog')?.close();const key=(context.operation+' '+context.screen).toLowerCase();if(admin()){if(/pairing|zigbee/.test(key))return openZigbee();if(/integrations|connection|coordinator/.test(key))return manageIntegrations();if(/backup|recover|restore/.test(key))return openRecovery();if(/remote|tailscale/.test(key))return openRemoteAccess();if(/household|account/.test(key))return openHousehold()}if(/command/.test(key)){navigate(state.room?'room':'home',state.room);return refreshSnapshot()}navigate('care');return refreshSnapshot()},signin:connection,setup:()=>admin()?navigate('manage'):connection(),refresh:()=>{if(client.connected)refreshSnapshot();else if(client.access)client.open();else connection()}});
const request=client.request.bind(client);client.request=(operation,payload={})=>ui.task(operation,request(operation,payload),{readOnly:/^(bootstrap|snapshot|discover|history|care|activity|camera\/snapshot|.*\/(?:status|list|library|me|traces))$/.test(operation),retry:()=>client.request(operation,payload)});
const status=client.onstatus;client.onstatus=(message,connected)=>{status(message,connected);ui.connection(connected,message)};
const login=client.onlogin;client.onlogin=()=>{ui.captureDrafts();login()};
const error=dialogError;dialogError=function(value){error(value);if(['invalid_password','invalid_auth'].includes(value.code))ui.fieldError(document.querySelector('#dialog input[type=password]'),errorText(value))};
})();
'''
personal=r'''
(()=>{const ui=window.VAutomateUI;
ui.init({scope:()=>typeof suite!=='undefined'&&suite.user?.id?'personal:'+location.origin+':'+(window.__VA_HOME_PROFILE__||'')+':'+suite.user.id:'',connected:()=>connected,hasSession:()=>!!(connected||token||states.length),checkStatus:context=>{ui.captureDrafts();if(!connected)return document.querySelector('#connect')?.click();document.querySelector('#modal')?.close();const key=(context.operation+' '+context.screen).toLowerCase();if(/history/.test(key))return go('History');if(isHomeAdmin()&&/backup|recover|update|zigbee|pair|integration|supervisor|log/.test(key)){platform.section=/backup|recover/.test(key)?'Backups':/update/.test(key)?'Updates':/pair|zigbee/.test(key)?'Devices':'Logs';suite.systemTab=platform.section;return go('System')}return go(view==='Rooms'?'Rooms':'Overview',view==='Rooms'?filter:'All')},signin:()=>document.querySelector('#connect')?.click(),setup:()=>document.querySelector('#settings')?.click(),refresh:()=>{ui.captureDrafts();if(connected&&typeof render==='function')render();else document.querySelector('#connect')?.click()}});
const nativeStatus=setStatus;setStatus=function(...args){const result=nativeStatus(...args);ui.connection(connected,String(args[0]||''));return result};
const wsRequest=platformWS;platformWS=function(type,data={},timeout){return ui.task(type,wsRequest(type,data,timeout),{readOnly:/get_|\/list$|\/get$|history|statistics|camera\/stream|auth\/current_user|frontend\/get_user_data|^automation\/config$/.test(type),retry:()=>platformWS(type,data,timeout)})};
const jsonRequest=platformJSON;platformJSON=function(path,method='GET',data){return ui.task(path,jsonRequest(path,method,data),{readOnly:method.toUpperCase()==='GET',retry:()=>platformJSON(path,method,data)})};
const clear=clearRefreshSession;clearRefreshSession=function(...args){ui.captureDrafts();return clear(...args)};
const connectError=connectionError;connectionError=function(message){const result=connectError(message);if(/sign.in.*(?:not accepted|expired)/i.test(message))ui.sessionExpired();else ui.connection(false,message);return result};
const auth=authRequest;authRequest=function(...args){return Promise.resolve(auth(...args)).catch(error=>{if(/invalid|incorrect|not accepted/i.test((error.code||'')+' '+error.message))ui.fieldError(document.querySelector('dialog[open] input[type=password]'),error.message);throw error})};
const notify=notifyFailure;notifyFailure=function(error,context){const result=notify(error,context);const friendly=typeof friendlyError==='function'?friendlyError(error):error;ui.failure({code:error?.code,message:friendly.message||String(error)});return result};
})();
'''
for folder,hook,style in [(project/'frontend',studio,'studio.css'),(workspace/'outputs/VAutomate',personal,'style.css'),(workspace/'outputs/VAutomate-Customer',personal,'style.css')]:
    file=folder/'app.js'
    if not file.exists():continue
    base=file.read_text(encoding='utf-8').split(marker)[0].rstrip()
    file.write_text(base+'\n\n'+marker+'\n'+common+'\n'+hook+'\n/* VA_SHARED_UI_STATES_END */\n',encoding='utf-8',newline='\n')
    file=folder/style;existing=file.read_text(encoding='utf-8');base=existing.split(css_marker)[0].rstrip();tail=existing.split(css_marker,1)[1].lstrip() if css_marker in existing else '';end='/* VA_SHARED_UI_STATES_CSS_END */';suffix=tail.split(end,1)[1] if end in tail else tail[len(css):] if tail.startswith(css) else '';file.write_text(base+'\n'+css_marker+'\n'+css+'\n'+end+'\n'+suffix.lstrip(),encoding='utf-8',newline='\n')
print('Shared UI states synchronized into Personal, Studio and legacy customer canonical assets.')
