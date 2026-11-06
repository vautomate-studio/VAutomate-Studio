/* VA_DEVICE_ICONS_BEGIN */
window.VAutomateDeviceIcons=(()=>{
 const paths={light:'M9 18h6M10 21h4M8 14a6 6 0 1 1 8 0l-1 2H9z',fan:'M12 12c-1-4-1-8 2-9 3-1 5 2 3 5l-5 4Zm0 0c4-1 8 0 9 3 1 3-2 5-5 3l-4-6Zm0 0c1 4-1 8-4 9-3 0-5-3-3-6l7-3Z',heater:'M7 4h10v16H7zM9 2h6M9 22v-2m6 2v-2M10 9c3-3 0-4 2-5m-2 10c3-3 0-4 2-5',pump:'M3 10h4V7h10v10H7v-4H3m14-3h4v3h-4M9 20h6M11 17v3m2-3v3M12 9l2 3-2 3-2-3z',switch:'M9 3h6a6 6 0 0 1 0 12H9A6 6 0 0 1 9 3ZM9 6a3 3 0 1 0 0 6 3 3 0 0 0 0-6ZM8 20h8',cover:'M3 4h18M5 4v16l7-5 7 5V4M12 4v11',climate:'M14 14V5a3 3 0 0 0-6 0v9a5 5 0 1 0 6 0M11 7v10',scene:'m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z',media_player:'M3 4h18v13H3zM8 21h8M12 17v4',generic:'M5 5h14v14H5zM9 9h6v6H9z'};
 function kind(s){const d=String(s?.entity_id||'').split('.')[0],a=s?.attributes||{},hint=String(a.icon||'').toLowerCase(),name=String((a.friendly_name||'')+' '+(s?.entity_id||'')).toLowerCase();if(['switch','water_heater'].includes(d)){if(/water.pump|pump|motor|bore/.test(hint+' '+name))return 'pump';if(/water.heater|geyser|geiser|boiler|heater/.test(hint+' '+name))return 'heater'}return ({input_boolean:'scene',script:'scene',automation:'scene',water_heater:'heater',humidifier:'climate'})[d]||(paths[d]?d:'generic')}
 function node(s){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');for(const [k,v] of Object.entries({viewBox:'0 0 24 24',fill:'none',stroke:'currentColor','stroke-width':'1.6','stroke-linecap':'round','stroke-linejoin':'round','aria-hidden':'true',class:'va-device-icon'}))svg.setAttribute(k,v);svg.dataset.iconKind=kind(s);const p=document.createElementNS(svg.namespaceURI,'path');p.setAttribute('d',paths[kind(s)]);svg.append(p);return svg}
 return {kind,node,html:s=>node(s).outerHTML};
})();
/* VA_DEVICE_ICONS_END */
/* Focused customer experience. Dynamic text is rendered as text, never executable HTML. */
'use strict';
const $=selector=>document.querySelector(selector);
const state={home:null,entities:new Map(),route:'home',room:null,loading:false,wizard:null,discovery:null,timer:null,dialogTimer:null,dirty:false,toastTimer:null,bootstrapEpoch:0,dialogEpoch:0};
const client=window.STUDIO_DEMO_CLIENT||new StudioClient();
const ICONS={home:'M3 11 12 3l9 8M5 10v11h14V10M9 21v-7h6v7',rooms:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',routines:'m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5z',care:'M3 12h4l3-7 4 14 3-7h4',light:'M9 18h6M9 21h6M8 14a6 6 0 1 1 8 0l-1 2H9z',fan:'M12 12c-1-4-1-8 2-9 3-1 5 2 3 5l-5 4Zm0 0c4-1 8 0 9 3 1 3-2 5-5 3l-4-6Zm0 0c1 4-1 8-4 9-3 0-5-3-3-6l7-3Z',switch:'M12 3v8M7 6a8 8 0 1 0 10 0',cover:'M3 4h18M5 4v16l7-5 7 5V4M12 4v11',climate:'M14 14V5a3 3 0 0 0-6 0v9a5 5 0 1 0 6 0M11 7v10',media_player:'M3 4h18v13H3zM8 21h8M12 17v4',alarm_control_panel:'m12 2 8 3v6c0 5-8 10-8 10S4 16 4 11V5zM9 11l2 2 4-5',camera:'M3 6h13v12H3zM16 10l5-3v10-5-3',sensor:'M4 12h4l2-7 4 14 2-7h4',binary_sensor:'M6 3h12v18H6zM10 12h.01',person:'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M4 21v-2a8 8 0 0 1 16 0v2',weather:'M12 3v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M12 19v2M5.6 18.4 7 17M17 7l1.4-1.4M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0',menu:'M4 6h16M4 12h16M4 18h16',arrow:'m9 5 6 7-6 7',check:'m5 12 4 4L19 6',plus:'M12 5v14M5 12h14',history:'M3 11a9 9 0 1 1 2 7M3 3v8h8M12 7v5l3 2'};
function element(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=String(text);return node}
function icon(name){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');svg.classList.add('icon');const p=document.createElementNS(svg.namespaceURI,'path');p.setAttribute('d',ICONS[name]||ICONS.routines);svg.append(p);return svg}
function button(label,callback,className=''){const b=element('button',className,label);b.type='button';b.onclick=callback;return b}
function iconButton(name,label,callback,className='icon-button'){const b=button('',callback,className);b.setAttribute('aria-label',label);b.title=label;b.append(icon(name));return b}
function field(label,value='',type='text'){const wrap=element('label','field',label);const input=element('input');input.type=type;input.value=value;input.setAttribute('aria-label',label);if(['Room name','Control name','Home name','Automation name','Person’s name'].includes(label))input.required=true;wrap.append(input);return {wrap,input}}
function selectField(label,options,value){const wrap=element('label','field',label),input=element('select');input.setAttribute('aria-label',label);for(const [v,l] of options){const opt=element('option','',l);opt.value=v;input.append(opt)}if(value!==undefined)input.value=value;wrap.append(input);return {wrap,input}}
function domain(id){return id.split('.')[0]}
/* STUDIO_PRESENTATION_BEGIN */
const StudioPresentation=(()=>{
 const sensors=new Set(['temperature','humidity','illuminance','occupancy','motion','presence','door','window','opening','smoke','carbon_monoxide','gas','moisture','safety','battery','power','energy','carbon_dioxide','pressure']);
 function everyday(entity,registry={}){if(!entity||entity.system||registry.disabled||registry.diagnostic)return false;const d=entity.entity_id.split('.')[0];if(['sensor','binary_sensor'].includes(d))return sensors.has(entity.attributes?.device_class)||['°C','°F','%','W','kW','kWh','lx'].includes(entity.attributes?.unit_of_measurement);return ['light','fan','switch','cover','climate','media_player','alarm_control_panel','camera','lock','person','weather','scene'].includes(d)}
 function removeRoom(layout,id){const next=structuredClone(layout);next.rooms=next.rooms.filter(r=>r.id!==id);if(next.cards)next.cards=next.cards.filter(c=>c.kind!=='room'||c.room_id!==id);return next}
 function personal(base,value,allowed){if(!value||value.schema!==1)return base;const rooms=new Set(base.rooms.map(r=>r.id)),cards=[],ids=new Set();for(const c of Array.isArray(value.cards)?value.cards.slice(0,40):[]){if(!c||typeof c.id!=='string'||!/^[-a-zA-Z0-9_]{1,80}$/.test(c.id)||ids.has(c.id)||![1,2,3].includes(c.span))continue;if(c.kind==='room'&&!rooms.has(c.room_id)||c.kind==='entity'&&!allowed.has(c.entity_id)||!['room','entity'].includes(c.kind))continue;ids.add(c.id);cards.push({id:c.id,kind:c.kind,span:c.span,...(c.kind==='room'?{room_id:c.room_id}:{entity_id:c.entity_id}),...(typeof c.title==='string'&&c.title.trim()?{title:c.title.trim().slice(0,80)}:{})})}return {...base,cards,cards_title:typeof value.cards_title==='string'&&value.cards_title.trim()?value.cards_title.trim().slice(0,80):base.cards_title,show_rooms:typeof value.show_rooms==='boolean'?value.show_rooms:base.show_rooms}}
 return {everyday,removeRoom,personal};
})();
/* STUDIO_PRESENTATION_END */
function presentationKey(){return 'vautomate-studio-commercial:view:'+location.origin+':'+(window.__VA_HOME_PROFILE__||'')+':'+state.home.user.id}
function memberCardEligible(s){return StudioPresentation.everyday(s)||state.home.layout.quick_actions.some(q=>q.entity_id===s.entity_id)}
function dashboardLayout(){const base=state.home.layout;if(admin())return base;let saved;try{saved=JSON.parse(localStorage.getItem(presentationKey())||'null')}catch{}return StudioPresentation.personal(base,saved,new Set([...state.entities.values()].filter(memberCardEligible).map(s=>s.entity_id)))}
async function saveDashboardView(layout){if(admin())return saveManagedLayout(layout,state.home.revision);localStorage.setItem(presentationKey(),JSON.stringify({schema:1,cards:layout.cards||[],cards_title:layout.cards_title,show_rooms:layout.show_rooms}));window.VAutomateUI?.clearFields();render();toast('Your dashboard is saved on this device. Shared rooms and devices are unchanged.')}
function deviceKind(entity){return ({light:'Lights',fan:'Fans',switch:'Switches',cover:'Curtains',climate:'Climate',media_player:'Media',alarm_control_panel:'Security',camera:'Cameras',sensor:'Readings',binary_sensor:'Safety & presence',person:'People',weather:'Weather',scene:'Scenes',input_boolean:'Home modes'})[domain(entity.entity_id)]||'System'}

function entityName(s){return s?.attributes?.friendly_name||s?.entity_id?.split('.')[1]?.replaceAll('_',' ')||'Device'}
function online(s){return s&&!['unknown','unavailable'].includes(s.state)}
function labelState(s){if(s&&domain(s.entity_id)==='weather'&&window.VAutomateWeather)return VAutomateWeather.present(s).label;if(!online(s))return 'Offline';if(domain(s.entity_id)==='scene')return 'Ready';const d=domain(s.entity_id);if(d==='person')return s.state==='home'?'Home':s.state==='not_home'?'Away':s.state.replaceAll('_',' ');if(d==='binary_sensor'){const open=['door','window','opening'].includes(s.attributes.device_class);return s.state==='on'?(open?'Open':'Detected'):(open?'Closed':'Clear')}return ({on:'On',off:'Off',armed_home:'Armed home',armed_away:'Armed away',armed_night:'Armed night',disarmed:'Disarmed',idle:'Idle',playing:'Playing',paused:'Paused'})[s.state]||String(s.state).replaceAll('_',' ')}
function entitiesFor(room){return room.entities.map(id=>state.entities.get(id)).filter(Boolean)}
function admin(){return state.home?.user.can_edit===true}
function controlsAllowed(){return client.connected&&!state.home?.read_only}
function toast(message){clearTimeout(state.toastTimer);$('#toast').textContent=message;$('#toast').classList.add('show');state.toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),5000)}
function errorText(error){if(error.code==='unknown_command')return 'Your installer needs to connect the VAutomate Studio service on this home.';return error.message||'Your home could not complete this request.'}
function showDialog(title,description){state.dialogEpoch++;clearInterval(state.dialogTimer);state.dialogTimer=null;const root=$('#dialog-content');delete root.dataset.vaDraftKey;delete root.dataset.vaModelEditor;delete root.dataset.vaEditor;root.replaceChildren();if(title)root.append(element('h2','',title));if(description)root.append(element('p','',description));const err=element('p','dialog-error');err.id='dialog-error';err.setAttribute('role','alert');root.append(err);if(!$('#dialog').open)$('#dialog').showModal();return root}
function clearPasswords(){for(const input of $('#dialog').querySelectorAll('input[type=password],input[name=code]'))input.value=''}
function closeDialog(){if(state.dirty&&state.wizard){if(!confirm('Keep your saved draft and close this editor?'))return}clearInterval(state.dialogTimer);state.dialogTimer=null;clearPasswords();$('#dialog').close();state.dirty=false;state.wizard=null}
function dialogError(error){$('#dialog-error').textContent=errorText(error)}
function heading(title,description,action){const row=element('div','page-heading'),copy=element('div');copy.append(element('div','eyebrow',state.home?.layout.name||'VAUTOMATE STUDIO'),element('h1','',title),element('p','',description));row.append(copy);if(action)row.append(action);return row}
function section(title,subtitle=''){const row=element('div','section-heading');row.append(element('h2','',title));if(subtitle)row.append(element('span','caption',subtitle));return row}
function empty(title,description,action){const box=element('section','panel empty-state');box.append(icon('home'),element('h2','',title),element('p','',description));if(action)box.append(action);return box}
function setConnection(message,connected){$('#connection').classList.toggle('connected',connected);$('#connection span').textContent=message;document.body.classList.toggle('disconnected',!connected);updateLive()}
function banner(){const box=$('#status-banner');if(window.STUDIO_DEMO_CLIENT){box.hidden=false;box.textContent='SHOWROOM · Simulated devices. Nothing connects to or operates your home.'}else if(state.home?.compatibility.status==='unsupported_core'){box.hidden=false;box.textContent=state.home.compatibility.message}else if(state.home?.read_only){box.hidden=false;box.textContent='Read-only evaluation · Live readings are available. Device commands are disabled.'}else if(state.home?.compatibility.certified===false&&admin()&&['care','manage'].includes(state.route)){box.hidden=false;box.textContent='Commissioning evaluation · This installation has not completed commercial release testing.'}else box.hidden=true}
function navigate(route,room){location.hash='#/'+route+(room?'/'+encodeURIComponent(room):'')}
function readRoute(){const parts=location.hash.slice(2).split('/');state.route=['home','rooms','room','routines','care','manage'].includes(parts[0])?parts[0]:'home';try{state.room=decodeURIComponent(parts[1]||'')}catch{state.room=''}render();document.body.classList.remove('sidebar-open');$('#scrim').hidden=true;$('#menu-toggle').setAttribute('aria-expanded','false');window.scrollTo({top:0,behavior:'instant'})}
function navigation(){const nav=$('#navigation');nav.replaceChildren();for(const [route,label,mark] of [['home','Home','home'],['rooms','Rooms','rooms'],['routines','Routines','routines'],['care','Home Care','care'],...(admin()?[['manage','Manage home','rooms']]:[])]){const b=button('',()=>navigate(route),state.route===route||state.route==='room'&&route==='rooms'?'selected':'');b.setAttribute('aria-label',label);b.append(icon(mark),element('span','',label));nav.append(b)}}
function render(){navigation();banner();const page=$('#page');page.replaceChildren();page.classList.remove('page-enter');void page.offsetWidth;page.classList.add('page-enter');if(!state.home){page.append(empty('Your home starts here.','Sign in to your VAutomate home to see its rooms, devices and routines.',button('Sign in',connection,'primary')));return}$('#account-button').textContent=(state.home.user.name||'V').slice(0,1).toUpperCase();if(state.route==='rooms')renderRooms(page);else if(state.route==='room')renderRoom(page);else if(state.route==='routines')renderRoutines(page);else if(state.route==='manage')renderManagement(page);else if(state.route==='care')renderCare(page);else renderHome(page);updateLive()}
function master(room,category){const ids=room.entities.filter(id=>domain(id)===category);if(!ids.length)return null;const b=iconButton(category,`Toggle all ${category==='light'?'lights':category==='fan'?'fans':'switches'} in ${room.name}`,()=>runCommand(b,{room_id:room.id,category}),'round-control');b.dataset.roomMaster=room.id;b.dataset.category=category;const mark=b.querySelector('svg');if(mark){mark.classList.add('va-device-icon');mark.dataset.iconKind=category}return b}
function roomCard(room){const box=element('article','panel room-card');box.dataset.roomCard=room.id;box.append(button('',()=>navigate('room',room.id),'room-link'));box.firstChild.setAttribute('aria-label','Open '+room.name);box.append(element('h3','',room.name));const meta=element('div','room-meta');meta.dataset.roomMeta=room.id;box.append(meta);const arrow=element('span','room-arrow');arrow.append(icon('arrow'));box.append(arrow);const row=element('div','room-controls');for(const cat of ['light','fan','switch']){const b=master(room,cat);if(b)row.append(b)}box.append(row);return box}
function updateWeatherReading(item,s){const weather=window.VAutomateWeather?.present(s,{connected:client.connected});if(!weather)return;if(item.dataset.condition!==weather.icon){item.querySelector('.weather-icon').replaceChildren(VAutomateWeather.createIcon(weather));item.dataset.condition=weather.icon}item.querySelector('.weather-condition').textContent=weather.label;item.querySelector('.weather-temperature').textContent=weather.temperature===null?'—':new Intl.NumberFormat(undefined,{maximumFractionDigits:1}).format(weather.temperature)+weather.unit;const details=[];if(weather.humidity!==null)details.push('Humidity '+weather.humidity+'%');if(weather.wind!==null)details.push('Wind '+weather.wind+' '+weather.windUnit);item.querySelector('.weather-facts').textContent=details.join(' · ');const time=weather.updatedAt?new Date(weather.updatedAt):null;item.querySelector('.weather-updated').textContent=!client.connected?'Last known conditions':time&&Number.isFinite(time.getTime())?'Updated '+time.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}):'Reported by your home'}
function weatherReading(s){const item=element('article','panel weather-reading weather-panel');item.dataset.weatherFor=s.entity_id;const symbol=element('span','weather-icon');item.append(element('span','weather-location',entityName(s)),symbol,element('strong','weather-temperature'),element('span','weather-condition'),element('small','weather-facts'),element('small','weather-updated'));updateWeatherReading(item,s);return item}
function renderHome(page){const greeting='Welcome home.';page.append(heading(greeting,state.home.layout.subtitle,admin()?button('Personalize',manageDashboard,'quiet'):button('Edit my dashboard',manageDashboard,'quiet')));const context=[...state.entities.values()];const weather=context.find(s=>domain(s.entity_id)==='weather'),people=context.filter(s=>domain(s.entity_id)==='person'),alarms=context.filter(s=>domain(s.entity_id)==='alarm_control_panel');if(weather||people.length||alarms.length){const lead=element('section','home-lead');if(weather)lead.append(weatherReading(weather));if(people.length||alarms.length){const panel=element('article','panel people-panel');panel.append(element('span','eyebrow','The people who make it home'));if(people.length){const row=element('div','people-row');for(const person of people){const item=element('div','person-status'),avatar=element('span','person-avatar',entityName(person).split(/\s+/).slice(0,2).map(w=>w[0]).join('').toUpperCase());avatar.dataset.personAvatar=person.entity_id;item.append(avatar,element('strong','',entityName(person)));const status=element('small','',labelState(person));status.dataset.statusFor=person.entity_id;item.append(status);row.append(item)}panel.append(row)}for(const alarm of alarms){const row=element('div','home-security');row.append(icon('alarm_control_panel'));const copy=element('div');copy.append(element('strong','','Home security'));const status=element('small','',labelState(alarm));status.dataset.statusFor=alarm.entity_id;copy.append(status);row.append(copy,button('Manage',()=>alarmDialog(state.entities.get(alarm.entity_id)),'quiet'));panel.append(row)}lead.append(panel)}page.append(lead)}if(state.home.layout.quick_actions.length){page.append(section('Make yourself at home.'));const row=element('div','quick-grid');for(const q of state.home.layout.quick_actions){const s=state.entities.get(q.entity_id);if(!s)continue;const b=button('',()=>{const current=state.entities.get(q.entity_id);runCommand(b,{entity_id:current.entity_id,action:domain(current.entity_id)==='scene'?'turn_on':current.state==='on'?'turn_off':'turn_on',data:{},...(domain(current.entity_id)==='scene'?{}:{expected_state:current.state})})},'quick-action');b.dataset.quickEntity=s.entity_id;b.append(icon(domain(s.entity_id)==='scene'?'routines':'switch'),element('span','',q.label));row.append(b)}page.append(row)}renderHomeCards(page);if(dashboardLayout().show_rooms===false)return;page.append(section('Your rooms.',state.home.layout.rooms.length+(state.home.layout.rooms.length===1?' space':' spaces')));const grid=element('div','grid');for(const room of state.home.layout.rooms)grid.append(roomCard(room));page.append(grid);if(!state.home.layout.rooms.length)page.append(empty('A home made yours.','Your installer can select the rooms and devices that belong on your dashboard.',admin()?button('Set up this home',openSetup,'primary'):null))}
function renderRooms(page){page.append(heading('Room to feel at home.','Choose a space. Everything you need is inside.',admin()?button('Organize rooms',manageRooms,'quiet'):null));const grid=element('div','grid');for(const room of state.home.layout.rooms)grid.append(roomCard(room));page.append(grid)}
function renderRoom(page){const room=state.home.layout.rooms.find(r=>r.id===state.room);if(!room){page.append(empty('This room has moved.','Return to your rooms to find its current place.',button('View rooms',()=>navigate('rooms'),'primary')));return}page.append(heading(room.name,'A little comfort. Exactly where you need it.'));const items=entitiesFor(room).filter(s=>admin()&&state.showSystem||StudioPresentation.everyday(s));if(admin())page.append(button(state.showSystem?'Hide system entities':'Show system entities',()=>{state.showSystem=!state.showSystem;render()},'quiet'));const readings=items.filter(s=>['sensor','binary_sensor'].includes(domain(s.entity_id)));if(readings.length){const row=element('div','reading-row');for(const s of readings){const reading=element('div','reading');if(domain(s.entity_id)==='binary_sensor'){reading.dataset.binaryReading=s.entity_id;reading.hidden=s.state!=='on'}const wrap=element('div'),value=element('strong','',s.state+' '+(s.attributes.unit_of_measurement||''));if(domain(s.entity_id)==='binary_sensor')value.textContent=['door','window','opening'].includes(s.attributes.device_class)?'Open':'Detected';else value.dataset.valueFor=s.entity_id;wrap.append(value,element('small','',entityName(s)));reading.append(icon(domain(s.entity_id)),wrap);row.append(reading)}page.append(row)}const masters=element('div','room-masters');for(const category of ['light','fan','switch']){const m=master(room,category);if(m)masters.append(m)}page.append(masters);const controls=items.filter(s=>!['sensor','binary_sensor'].includes(domain(s.entity_id)));const groups=[['Lights',s=>domain(s.entity_id)==='light'],['Fans',s=>domain(s.entity_id)==='fan'],['Comfort',s=>['climate','cover','humidifier','water_heater'].includes(domain(s.entity_id))],['Switches & appliances',s=>domain(s.entity_id)==='switch'],['Scenes',s=>['scene','script','input_boolean'].includes(domain(s.entity_id))],['Other controls',s=>!['light','fan','climate','cover','humidifier','water_heater','switch','scene','script','input_boolean'].includes(domain(s.entity_id))]];for(const [label,match] of groups){const members=controls.filter(match);if(!members.length)continue;page.append(section(label));const grid=element('div','grid compact');for(const item of members)grid.append(deviceCard(item));page.append(grid)}}
function deviceCard(s){const box=element('article','panel device');box.dataset.deviceCard=s.entity_id;const top=element('div','device-head'),copy=element('div'),name=element('h3','',entityName(s)),status=element('div','device-status',labelState(s));status.dataset.statusFor=s.entity_id;copy.append(name,status);top.append(window.VAutomateDeviceIcons.node(s),copy);const ops=s.operations||{},d=domain(s.entity_id);if(['light','switch','fan','input_boolean'].includes(d)&&(ops.turn_on||ops.turn_off)){const toggle=button('',()=>{const current=state.entities.get(s.entity_id);runCommand(toggle,{entity_id:s.entity_id,action:current.state==='on'?'turn_off':'turn_on',data:{},expected_state:current.state})},'switch');toggle.setAttribute('role','switch');toggle.setAttribute('aria-label',entityName(s));toggle.dataset.powerFor=s.entity_id;top.append(toggle)}box.append(top);const body=element('div','device-actions');
 const actions=d==='cover'?[['open_cover','Open'],['stop_cover','Stop'],['close_cover','Close']]:d==='media_player'?[['media_play','Play'],['media_pause','Pause'],['turn_on','On'],['turn_off','Off']]:d==='scene'?[['turn_on','Activate']]:[];
 for(const [action,label] of actions)if(ops[action]){const b=button(label,()=>runCommand(b,{entity_id:s.entity_id,action,data:{}}));b.dataset.actuator='';body.append(b)}
 if(d==='alarm_control_panel')body.append(button('Security controls',()=>alarmDialog(state.entities.get(s.entity_id))));
 if(d==='camera')body.append(button('View camera',()=>cameraDialog(s)));
 if(ops.turn_on?.includes('brightness_pct'))box.append(rangeControl(s,'Brightness','brightness_pct',0,100,Math.round((s.attributes.brightness||0)/255*100),'turn_on','%'));
 if(ops.set_cover_position)box.append(rangeControl(s,'Position','position',0,100,s.attributes.current_position||0,'set_cover_position','%'));
 if(ops.set_percentage)box.append(rangeControl(s,'Fan speed','percentage',0,100,s.attributes.percentage||0,'set_percentage','%'));
 if(ops.volume_set)box.append(rangeControl(s,'Volume','volume_level',0,100,Math.round((s.attributes.volume_level||0)*100),'volume_set','%',100));
 if(ops.set_temperature)box.append(rangeControl(s,'Temperature','temperature',s.attributes.min_temp||7,s.attributes.max_temp||35,s.attributes.temperature||s.attributes.current_temperature||22,'set_temperature','°'));
 if(ops.select_source){const sel=selectField('Source',(s.attributes.source_list||[]).map(x=>[x,x]),s.attributes.source);sel.input.dataset.actuator='';sel.input.onchange=()=>runCommand(sel.input,{entity_id:s.entity_id,action:'select_source',data:{source:sel.input.value}});box.append(sel.wrap)}
 if(ops.set_hvac_mode){const sel=selectField('Mode',(s.attributes.hvac_modes||[]).map(x=>[x,x.replaceAll('_',' ')]),s.state);sel.input.dataset.actuator='';sel.input.onchange=()=>runCommand(sel.input,{entity_id:s.entity_id,action:'set_hvac_mode',data:{hvac_mode:sel.input.value}});box.append(sel.wrap)}
 body.append(iconButton('history','Device history',()=>deviceDetails(state.entities.get(s.entity_id))));box.append(body);return box}
function rangeControl(s,label,key,min,max,value,action,suffix,divisor=1){const wrap=element('label','range-field',label),input=element('input'),output=element('output','',Math.round(value)+suffix);input.type='range';input.min=min;input.max=max;input.step=key==='temperature'?(s.attributes.target_temp_step||.5):1;input.value=value;input.setAttribute('aria-label',label+' · '+entityName(s));input.dataset.rangeFor=s.entity_id;input.dataset.valueKey=key;input.dataset.divisor=divisor;input.dataset.actuator='';input.oninput=()=>{output.textContent=input.value+suffix};input.onchange=()=>runCommand(input,{entity_id:s.entity_id,action,data:{[key]:Number(input.value)/divisor}});wrap.append(input,output);return wrap}
function updateLive(){for(const avatar of document.querySelectorAll('[data-person-avatar]'))avatar.classList.toggle('at-home',state.entities.get(avatar.dataset.personAvatar)?.state==='home');for(const item of document.querySelectorAll('[data-weather-for]')){const s=state.entities.get(item.dataset.weatherFor);if(s)updateWeatherReading(item,s)}for(const node of document.querySelectorAll('[data-binary-reading]'))node.hidden=state.entities.get(node.dataset.binaryReading)?.state!=='on';for(const node of document.querySelectorAll('[data-status-for]'))node.textContent=labelState(state.entities.get(node.dataset.statusFor));for(const node of document.querySelectorAll('[data-value-for]')){const s=state.entities.get(node.dataset.valueFor);if(s)node.textContent=s.state+' '+(s.attributes.unit_of_measurement||'')}for(const node of document.querySelectorAll('[data-device-card]'))node.classList.toggle('is-on',state.entities.get(node.dataset.deviceCard)?.state==='on');for(const node of document.querySelectorAll('[data-power-for]')){const s=state.entities.get(node.dataset.powerFor);node.setAttribute('aria-checked',s?.state==='on'?'true':'false');node.disabled=!controlsAllowed()||!online(s)||(s?.state==='on'?!s?.operations?.turn_off:!s?.operations?.turn_on)}for(const node of document.querySelectorAll('[data-quick-entity]')){const s=state.entities.get(node.dataset.quickEntity);node.classList.toggle('is-on',domain(node.dataset.quickEntity)==='input_boolean'&&s?.state==='on');node.disabled=!controlsAllowed()||!online(s)||(!s?.operations?.turn_on&&!s?.operations?.turn_off)}for(const node of document.querySelectorAll('[data-actuator]'))node.disabled=!controlsAllowed();for(const node of document.querySelectorAll('[data-room-master]')){const room=state.home?.layout.rooms.find(r=>r.id===node.dataset.roomMaster),items=room?entitiesFor(room).filter(s=>domain(s.entity_id)===node.dataset.category):[];const on=items.some(s=>s.state==='on');node.classList.toggle('is-on',on);node.setAttribute('aria-pressed',String(on));node.disabled=!controlsAllowed()||items.some(s=>!online(s)||!s.operations?.turn_on||!s.operations?.turn_off)}for(const node of document.querySelectorAll('[data-room-meta]')){const room=state.home?.layout.rooms.find(r=>r.id===node.dataset.roomMeta);if(!room)continue;const items=entitiesFor(room),on=items.filter(s=>['light','fan','switch'].includes(domain(s.entity_id))&&s.state==='on').length,offline=items.filter(s=>!online(s)).length,active=items.filter(s=>domain(s.entity_id)==='binary_sensor'&&s.state==='on');node.replaceChildren(element('span','caption',on?on+' on':'At rest'));if(offline)node.append(element('span','caption',offline+' offline'));for(const s of active.slice(0,2))node.append(element('span','presence-active',entityName(s)))}for(const node of document.querySelectorAll('[data-range-for]')){if(document.activeElement===node)continue;const s=state.entities.get(node.dataset.rangeFor);if(!s)continue;const key=node.dataset.valueKey;let value=key==='brightness_pct'?Math.round((s.attributes.brightness||0)/255*100):key==='position'?s.attributes.current_position:s.attributes[key];if(value!==undefined){node.value=value*Number(node.dataset.divisor||1);node.nextElementSibling.textContent=node.value+(key==='temperature'?'°':'%')}}}
async function runCommand(control,payload){if(control.classList.contains('pending'))return;control.classList.add('pending');control.setAttribute('aria-busy','true');try{const result=await client.command(payload);if(result.status==='check_required')toast('Some devices need checking. Their current states will update shortly.');else if(result.status==='pending')toast('Your home is already handling this request.');else toast('Requested. Waiting for the device to confirm.');await refreshSnapshot()}catch(error){toast(errorText(error))}finally{control.classList.remove('pending');control.removeAttribute('aria-busy');updateLive()}}
async function refreshSnapshot(){if(!client.connected||!state.home||state.loading||document.hidden)return;state.loading=true;try{const result=await client.request('snapshot');for(const s of result.entities)state.entities.set(s.entity_id,s);if(result.revision!==state.home.revision&&!$('#dialog').open)await bootstrap();else updateLive()}catch(error){if(!['offline','connection_lost'].includes(error.code))toast(errorText(error))}finally{state.loading=false}}
async function bootstrap(){const epoch=++state.bootstrapEpoch;try{const home=await client.request('bootstrap');if(epoch!==state.bootstrapEpoch)return;if(home.api_version!==1||!home.user||!home.layout||!Array.isArray(home.layout.rooms)||!Array.isArray(home.layout.quick_actions)||!Array.isArray(home.entities)||!home.compatibility)throw new StudioError('incompatible','This home needs a compatible VAutomate app update.');state.home=home;client.serverOffset=home.server_time*1000-Date.now();state.entities=new Map(home.entities.map(s=>[s.entity_id,s]));$('#dialog').close();render();clearInterval(state.timer);state.timer=setInterval(refreshSnapshot,3000)}catch(error){if(state.home){window.VAutomateUI?.failure(error,{readOnly:true,retry:bootstrap});return}state.home=null;setConnection('Installer setup needed',false);render();showDialog('Let’s connect your home.',errorText(error));if(error.code==='unknown_command')$('#dialog-content').append(element('p','caption','This separate commercial service has not been installed. Your existing home and personal dashboard have not been changed.'));else $('#dialog-content').append(button('Try again',bootstrap,'primary'))}}
function alarmDialog(s){const root=showDialog('Home security.',entityName(s)+' · '+labelState(s));const code=field('Security code','','password');code.input.autocomplete='off';code.input.dataset.transient='';code.input.inputMode=s.attributes.code_format==='number'?'numeric':'text';if(s.attributes.code_format)root.append(code.wrap);const row=element('div','form-row');for(const [action,label] of [['alarm_arm_home','Arm home'],['alarm_arm_away','Arm away'],['alarm_arm_night','Arm night'],['alarm_disarm','Disarm']])if(s.operations[action]){const b=button(label,async()=>{b.disabled=true;const value=code.input.value;code.input.value='';try{const result=await client.command({entity_id:s.entity_id,action,data:value?{code:value}:{},expected_state:state.entities.get(s.entity_id)?.state});if(result.status!=='accepted')throw Error('Security status needs checking. Review the current alarm state before trying again.');$('#dialog').close();toast('Security request sent. Waiting for confirmation.');await refreshSnapshot()}catch(error){dialogError(error)}finally{b.disabled=!controlsAllowed()}},action==='alarm_disarm'?'primary':'');b.disabled=!controlsAllowed();row.append(b)}root.append(row,element('p','caption','Codes are used for this request only. They are never saved in your layout or activity log.'))}
async function deviceDetails(s){const root=showDialog(entityName(s),labelState(s));const readout=element('p','chart-readout','Choose a point on the graph to see its time and value.');root.append(readout);try{const result=await client.request('history',{entity_id:s.entity_id,hours:24});if(!result.points?.length){root.append(element('p','caption','No recorded readings are available for the last 24 hours.'));return}const canvas=element('canvas','chart');canvas.width=900;canvas.height=300;canvas.setAttribute('aria-label','Last 24 hours. Touch or use left and right arrows to inspect readings.');canvas.tabIndex=0;root.append(canvas);drawHistory(canvas,result.points,readout,s.attributes.unit_of_measurement||'')}catch(error){root.append(element('p','caption',errorText(error)))}}
function drawHistory(canvas,points,readout,unit){const numeric=points.filter(p=>Number.isFinite(Number(p.value)));if(!numeric.length){readout.textContent='This device records events rather than numeric readings.';for(const p of points.slice(-12).reverse())canvas.parentNode.append(element('p','caption',new Date(p.time*1000).toLocaleString()+' · '+p.value));canvas.remove();return}let selected=numeric.length-1;const ctx=canvas.getContext('2d');const min=Math.min(...numeric.map(p=>Number(p.value))),max=Math.max(...numeric.map(p=>Number(p.value))),start=numeric[0].time,end=numeric.at(-1).time;function draw(){ctx.clearRect(0,0,900,300);ctx.strokeStyle=getComputedStyle(document.body).getPropertyValue('--accent');ctx.lineWidth=3;ctx.beginPath();numeric.forEach((p,i)=>{const x=20+(p.time-start)/(end-start||1)*860,y=270-(Number(p.value)-min)/(max-min||1)*240;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();const p=numeric[selected],x=20+(p.time-start)/(end-start||1)*860;ctx.globalAlpha=.3;ctx.beginPath();ctx.moveTo(x,15);ctx.lineTo(x,280);ctx.stroke();ctx.globalAlpha=1;readout.textContent=new Date(p.time*1000).toLocaleString()+' · '+p.value+' '+unit}function at(event){const rect=canvas.getBoundingClientRect(),target=start+Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width))*(end-start);selected=numeric.reduce((best,p,i)=>Math.abs(p.time-target)<Math.abs(numeric[best].time-target)?i:best,0);draw()}canvas.onpointerdown=event=>{canvas.setPointerCapture(event.pointerId);at(event)};canvas.onpointermove=event=>{if(event.buttons||event.pointerType==='mouse')at(event)};canvas.onkeydown=event=>{if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();event.stopPropagation();selected=Math.max(0,Math.min(numeric.length-1,selected+(event.key==='ArrowRight'?1:-1)));draw()}};draw()}
function cameraDialog(s){const root=showDialog(entityName(s),'Camera snapshots · Live-video certification is pending for this release.'),frame=element('div','camera-frame'),image=element('img','camera-preview');image.alt=entityName(s);frame.append(image);root.append(frame,button('Full screen',async()=>{try{await frame.requestFullscreen()}catch{toast('Full screen is unavailable on this device.')}}));let busy=false;async function update(){if(busy||!$('#dialog').open)return;busy=true;try{const result=await client.request('camera/snapshot',{entity_id:s.entity_id});image.src='data:'+result.content_type+';base64,'+result.image}catch(error){dialogError(error)}finally{busy=false}}update();state.dialogTimer=setInterval(update,4000)}
function draftKey(){return 'vautomate-studio-commercial:draft:'+(window.__VA_HOME_PROFILE__||location.origin)+':'+state.home.user.id}
async function openSetup(){if(!admin())return;showDialog('Meeting your home.','Finding available devices and rooms…');try{state.discovery=await client.request('discover');let saved;try{saved=JSON.parse(localStorage.getItem(draftKey())||'null')}catch{}state.wizard={step:0,layout:saved?.revision===state.home.revision?saved.layout:structuredClone(state.home.layout),revision:state.home.revision};drawSetup()}catch(error){dialogError(error)}}
function saveDraft(){state.dirty=true;try{localStorage.setItem(draftKey(),JSON.stringify({revision:state.wizard.revision,layout:state.wizard.layout}))}catch{toast('This device could not save your draft. Keep the editor open.')}}
function drawSetup(){const wizard=state.wizard;if(!wizard)return;const layout=wizard.layout,root=showDialog(['Make it yours.','Familiar spaces.','Your Home buttons.','Ready for your home?'][wizard.step],['Choose a name and welcome line.','Select only the devices that belong in each room.','Choose up to four scenes or persistent home modes.','Review before sharing this VAutomate layout with your household.'][wizard.step]);const progress=element('div','wizard-progress');for(let i=0;i<4;i++)progress.append(element('i',i<=wizard.step?'active':''));root.prepend(progress);
 if(wizard.step===0){for(const [key,label] of [['name','Home name'],['subtitle','Welcome line']]){const f=field(label,layout[key]);f.input.maxLength=key==='name'?80:160;f.input.oninput=()=>{layout[key]=f.input.value;saveDraft()};root.append(f.wrap)}if(!layout.rooms.length&&state.discovery.areas.length)root.append(button('Start with existing rooms',()=>{for(const area of state.discovery.areas){const registered=state.discovery.registry.filter(e=>!e.disabled&&!e.diagnostic&&(e.area_id===area.id||state.discovery.devices.some(d=>d.id===e.device_id&&d.area_id===area.id)));const ids=registered.map(e=>e.entity_id).filter(id=>state.discovery.entities.some(s=>s.entity_id===id&&StudioPresentation.everyday(s,registered.find(r=>r.entity_id===id))));if(ids.length)layout.rooms.push({id:uid(),name:area.name,entities:ids})}saveDraft();drawSetup()}))}
 if(wizard.step===1){if(!layout.rooms.length)root.append(button('Suggest rooms from my home',suggestRooms,'primary'),element('p','caption','We use your existing room assignments. Review every selection before sharing.'));for(const room of layout.rooms){const row=element('div','settings-row'),name=field('Room name',room.name);name.input.oninput=()=>{room.name=name.input.value;saveDraft()};row.append(name.wrap,button('Devices · '+room.entities.length,()=>selectRoomDevices(room)),iconButton('plus','Remove '+room.name,()=>{layout.rooms=layout.rooms.filter(r=>r.id!==room.id);saveDraft();drawSetup()}));row.lastChild.textContent='×';root.append(row)}root.append(button('Add a room',()=>{layout.rooms.push({id:uid(),name:'New room',entities:[]});saveDraft();drawSetup()}))}
 if(wizard.step===2){const candidates=state.discovery.entities.filter(s=>['scene','input_boolean'].includes(domain(s.entity_id)));for(let i=0;i<4;i++){const current=layout.quick_actions[i];const pick=selectField('Home button '+(i+1),[['','No button'],...candidates.map(s=>[s.entity_id,entityName(s)])],current?.entity_id||'');const name=field('Button label',current?.label||'');pick.input.onchange=()=>{if(pick.input.value){const s=candidates.find(s=>s.entity_id===pick.input.value);layout.quick_actions[i]={entity_id:pick.input.value,label:name.input.value||entityName(s)}}else layout.quick_actions.splice(i,1);layout.quick_actions=layout.quick_actions.filter(Boolean);saveDraft();drawSetup()};name.input.oninput=()=>{if(layout.quick_actions[i])layout.quick_actions[i].label=name.input.value;saveDraft()};root.append(pick.wrap,name.wrap)}}
 if(wizard.step===3){root.append(element('h3','',layout.name),element('p','',layout.subtitle));for(const room of layout.rooms)root.append(element('p','caption',room.name+' · '+room.entities.length+' selected devices'));root.append(element('p','caption','This publishes the Studio dashboard only. Existing Home Assistant dashboards, server areas, device names and automations are kept.'))}
 const actions=element('div','form-row');if(wizard.step>0)actions.append(button('Back',()=>{wizard.step--;drawSetup()}));actions.append(button(wizard.step===3?'Save for this home':'Continue',async()=>{if(wizard.step<3){wizard.step++;drawSetup();return}const b=actions.lastChild;b.disabled=true;try{await client.request('layout/preview',{layout});await client.request('layout/publish',{layout,revision:wizard.revision});localStorage.removeItem(draftKey());state.wizard=null;state.dirty=false;$('#dialog').close();await bootstrap();toast('Your VAutomate home is ready.')}catch(error){dialogError(error)}finally{b.disabled=false}},'primary'));root.append(actions)}
function uid(){return 'studio-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,10)}
function selectRoomDevices(room){const root=showDialog(room.name,'Choose the controls and readings customers should see in this room.');const search=field('Find a device');root.append(search.wrap);const list=element('div');root.append(list);function draw(){list.replaceChildren();for(const s of state.discovery.entities.filter(s=>StudioPresentation.everyday(s,state.discovery.registry?.find(r=>r.entity_id===s.entity_id))&&entityName(s).toLowerCase().includes(search.input.value.toLowerCase()))){const label=element('label','select-device'),checkbox=element('input');checkbox.type='checkbox';checkbox.checked=room.entities.includes(s.entity_id);checkbox.onchange=()=>{room.entities=checkbox.checked?[...new Set([...room.entities,s.entity_id])]:room.entities.filter(id=>id!==s.entity_id);saveDraft()};const copy=element('span','',entityName(s));copy.append(element('small','',({alarm_control_panel:'Home security',media_player:'Media',input_boolean:'Home mode',binary_sensor:'Status sensor',cover:'Curtain or blind'})[domain(s.entity_id)]||domain(s.entity_id)));label.append(checkbox,copy);list.append(label)}}search.input.oninput=draw;draw();root.append(button('Done',drawSetup,'primary'))}
function renderRoutines(page){page.append(heading('A home that fits your day.','Simple schedules. Clear actions. Always editable.',admin()?button('Explore library',browseBundles,'primary'):null));if(admin())page.append(button('Create a custom schedule',()=>routineEditor(),'quiet'));const grid=element('div','grid');for(const r of state.home.routines||[]){const card=element('section','panel');card.append(element('h3','',r.name),element('p','caption',r.time+' · '+(r.days.length===7?'Every day':r.days.map(d=>['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d]).join(', '))),element('p','caption',r.actions.length+' actions · '+(r.enabled?'Enabled':'Paused')));if(admin())card.append(button('Edit routine',()=>routineEditor(r)));grid.append(card)}page.append(grid);if(!state.home.routines?.length)page.append(empty('Small routines. Everyday comfort.','Schedule lights, curtains, fans and media without writing code.',admin()?button('Explore routines',browseBundles,'primary'):null))}

async function browseBundles(){
 const root=showDialog('Thoughtful routines. Yours to choose.','These suggestions are bundled with VAutomate. None are created or enabled automatically.');
 try{const result=await client.request('bundles/list');const grid=element('div','bundle-library');for(const bundle of result.bundles){const card=element('section','panel');card.append(element('h3','',bundle.name),element('p','caption',bundle.description),element('span','pill','Version '+bundle.version));if(result.can_create)card.append(button('Choose devices',()=>configureBundle(bundle),'primary'));grid.append(card)}root.append(grid)}catch(error){dialogError(error)}
}
function configureBundle(bundle,previous){
 const inputs=previous||{name:bundle.name,time:bundle.default_time,days:[0,1,2,3,4,5,6],targets:{}};
 const root=showDialog(bundle.name+'.',bundle.description),name=field('Routine name',inputs.name),time=field('Time at home',inputs.time,'time');
 name.input.maxLength=80;name.input.oninput=()=>inputs.name=name.input.value;time.input.onchange=()=>inputs.time=time.input.value;root.append(name.wrap,time.wrap,element('p','caption',"Schedules use your home's time zone."));
 const days=element('div','day-picker');for(let i=0;i<7;i++){const b=button(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i],()=>{inputs.days=inputs.days.includes(i)?inputs.days.filter(d=>d!==i):[...inputs.days,i];b.classList.toggle('primary',inputs.days.includes(i));b.setAttribute('aria-pressed',String(inputs.days.includes(i)))},inputs.days.includes(i)?'primary':'');b.setAttribute('aria-pressed',String(inputs.days.includes(i)));days.append(b)}root.append(days);
 for(const slot of bundle.slots){root.append(element('h3','bundle-slot-title',slot.label));const eligible=[...state.entities.values()].filter(s=>domain(s.entity_id)===slot.domain&&s.operations?.[slot.action]);if(!eligible.length)root.append(element('p','caption','No compatible devices have been added to this home for this choice.'));for(const entity of eligible){const label=element('label','select-device'),input=element('input');input.type='checkbox';input.checked=(inputs.targets[slot.id]||[]).includes(entity.entity_id);input.setAttribute('aria-label',slot.label+' · '+entityName(entity));input.onchange=()=>{const ids=inputs.targets[slot.id]||[];inputs.targets[slot.id]=input.checked?[...new Set([...ids,entity.entity_id])]:ids.filter(id=>id!==entity.entity_id)};label.append(input,element('span','',entityName(entity)));root.append(label)}}
 const review=button('Review routine',async()=>{review.disabled=true;try{const preview=await client.request('bundles/preview',{bundle_id:bundle.id,inputs,revision:state.home.revision});reviewBundle(bundle,inputs,preview)}catch(error){dialogError(error)}finally{review.disabled=false}},'primary');root.append(review,element('p','caption','Reviewing does not save a routine or operate any device.'));
}
function reviewBundle(bundle,inputs,preview){
 const root=showDialog('Review your routine.','Nothing has been created or switched on. Approve only if these choices are right for your home.');root.append(element('h3','',preview.routine.name),element('p','caption',preview.routine.time+' · '+preview.routine.days.map(d=>['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d]).join(', ')));
 const labels={turn_on:'Turn on',turn_off:'Turn off',open_cover:'Open',close_cover:'Close',media_pause:'Pause'};
 for(const action of preview.routine.actions)root.append(element('p','bundle-action',(labels[action.action]||action.action.replaceAll('_',' '))+' · '+entityName(state.entities.get(action.entity_id))));
 const enable=field('Enable after creating',undefined,'checkbox');enable.input.checked=false;enable.input.disabled=state.home.read_only;root.append(enable.wrap);
 const approve=button('Approve & create paused',async()=>{approve.disabled=true;try{const result=await client.request('bundles/approve',{approval_nonce:preview.approval_nonce,enabled:enable.input.checked});$('#dialog').close();await bootstrap();toast(result.enabled?'Approved routine created and enabled.':'Approved routine created paused. Enable it when you choose.')}catch(error){dialogError(error)}finally{approve.disabled=false}},'primary');
 enable.input.onchange=()=>approve.textContent=enable.input.checked?'Approve & enable':'Approve & create paused';root.append(element('p','caption','This creates your own editable copy. Library updates will never silently replace your choices.'),approve,button('Back to choices',()=>configureBundle(bundle,inputs),'quiet'));
}

function routineEditor(existing){if(!admin())return;const value=existing?structuredClone(existing):{id:uid(),name:'Evening comfort',time:'19:00',days:[0,1,2,3,4,5,6],enabled:false,actions:[]};delete value.owner_id;delete value.origin;let householdConsidered=false;function draw(){const root=showDialog('Your daily rhythm.','Choose a time and the things your home should do. Security commands cannot be scheduled here.');const name=field('Routine name',value.name),time=field('Time',value.time,'time');name.input.oninput=()=>value.name=name.input.value;time.input.onchange=()=>value.time=time.input.value;root.append(name.wrap,time.wrap);const days=element('div','day-picker');for(let i=0;i<7;i++){const b=button(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i],()=>{value.days=value.days.includes(i)?value.days.filter(d=>d!==i):[...value.days,i];draw()},value.days.includes(i)?'primary':'');days.append(b)}root.append(days);const enabled=field('Enabled',undefined,'checkbox');enabled.input.checked=value.enabled;enabled.input.onchange=()=>value.enabled=enabled.input.checked;root.append(enabled.wrap);for(let i=0;i<value.actions.length;i++){const action=value.actions[i],row=element('div','settings-row');row.append(element('span','',entityName(state.entities.get(action.entity_id))+' · '+action.action.replaceAll('_',' ')),button('Remove',()=>{value.actions.splice(i,1);draw()}));root.append(row)}root.append(button('Add an action',()=>routineAction(value,draw)));const save=button('Save routine',async()=>{if(!householdConsidered){dialogError(Error('Please consider the effect on other people at home before saving.'));return}save.disabled=true;try{await client.request('routine/save',{routine:value,revision:state.home.revision});$('#dialog').close();await bootstrap();toast('Routine saved.')}catch(error){dialogError(error)}finally{save.disabled=false}},'primary');const notice=element('section','shared-home-notice');notice.append(element('h3','','Consider everyone at home.'),element('p','','What feels right to you may disturb someone else. Discuss changes, respect privacy, keep manual controls available, and test before enabling.'));const acknowledge=field('I have considered other people at home',undefined,'checkbox');acknowledge.input.checked=householdConsidered;save.disabled=!householdConsidered;acknowledge.input.onchange=()=>{householdConsidered=acknowledge.input.checked;save.disabled=!householdConsidered};notice.append(acknowledge.wrap);root.append(notice,save);if(existing)root.append(button('Remove routine',async()=>{if(!confirm('Remove this routine from this home?'))return;try{await client.request('routine/remove',{routine_id:value.id,revision:state.home.revision});$('#dialog').close();await bootstrap();toast('Routine removed.')}catch(error){dialogError(error)}}))}draw()}
function routineAction(value,done){const root=showDialog('What should happen?','Select one supported device and action.');const candidates=[...state.entities.values()].filter(s=>['light','cover','switch','fan','climate','media_player','input_boolean'].includes(domain(s.entity_id))&&Object.keys(s.operations||{}).length);if(!candidates.length){root.append(element('p','caption','No supported controls have been added to this home yet.'));return}const device=selectField('Device',candidates.map(s=>[s.entity_id,entityName(s)])),action=selectField('Action',[]),fields=element('div');root.append(device.wrap,action.wrap,fields);function actions(){action.input.replaceChildren();const s=candidates.find(s=>s.entity_id===device.input.value);for(const key of Object.keys(s.operations)){const o=element('option','',key.replaceAll('_',' '));o.value=key;action.input.append(o)}parameters()}function parameters(){fields.replaceChildren();const s=candidates.find(s=>s.entity_id===device.input.value);for(const key of s.operations[action.input.value]||[]){if(['color_temp_kelvin','brightness_pct'].includes(key)&&action.input.value==='turn_on')continue;const f=key==='source'?selectField('Source',(s.attributes.source_list||[]).map(x=>[x,x])):key==='hvac_mode'?selectField('Mode',(s.attributes.hvac_modes||[]).map(x=>[x,x])):key==='is_volume_muted'?selectField('Mute',[['true','On'],['false','Off']]):field(key.replaceAll('_',' '),'','number');f.input.dataset.parameter=key;fields.append(f.wrap)}}device.input.onchange=actions;action.input.onchange=parameters;actions();root.append(button('Add to routine',()=>{const data={};for(const input of fields.querySelectorAll('[data-parameter]')){const k=input.dataset.parameter;data[k]=['source','hvac_mode'].includes(k)?input.value:k==='is_volume_muted'?input.value==='true':Number(input.value)}value.actions.push({entity_id:device.input.value,action:action.input.value,data});done()},'primary'))}
async function renderCare(page){if(admin()){const tools=element('div','device-actions');tools.append(button('Replace a device',openReplacement),button('Add a device',addDeviceHub,'primary'),button('Household access',openHousehold,'primary'),button('Backups & recovery',openRecovery),button('Installation status',installationStatus,'quiet'));page.append(tools)}page.append(heading('Your home, looked after.','Clear status and useful help. Technical work stays with your installer.'));const card=element('section','panel');card.append(element('h3','',client.connected?'Your home is connected.':'Your home is reconnecting.'),element('p','caption','VAutomate Studio '+state.home.bridge_version));page.append(card);if(admin()){const box=element('section','panel');box.append(element('h3','', 'Installation care'));page.append(section('For your installer.'),box);try{const data=await client.request('care');if(state.route!=='care')return;for(const check of data.checks){const row=element('div','settings-row');row.append(element('span','',check.name),element('span','pill',check.status.replaceAll('_',' ')));box.append(row)}box.append(element('p','caption','Software updates and device pairing still require commissioning validation. Backups and reviewed restoration are available above.'))}catch(error){box.append(element('p','caption',errorText(error)))}}const list=element('section','panel');page.append(section('Recent activity.'),list);try{const result=await client.request('activity');if(state.route!=='care')return;if(!result.items.length)list.append(element('p','caption','No activity recorded since this service started.'));for(const item of result.items.slice(0,30)){const row=element('div','activity-row'),copy=element('div','',(item.entity_id?entityName(state.entities.get(item.entity_id))+' · ':'')+item.action.replaceAll('_',' '));copy.append(element('small','', ' · '+item.outcome.replaceAll('_',' ')));row.append(copy,element('small','',new Date(item.time*1000).toLocaleTimeString()));list.append(row)}}catch(error){list.append(element('p','caption',errorText(error)))}}
function appearance(){const root=showDialog('A home in your colours.','Applied instantly. Your choice is remembered on this device.'),choices=element('div','theme-options');choices.setAttribute('role','radiogroup');choices.setAttribute('aria-label','Appearance theme');const current=()=>document.body.dataset.theme;function choose(id){document.body.dataset.theme=id;try{localStorage.setItem('vautomate-studio-commercial:theme',id)}catch{}for(const option of choices.querySelectorAll('button'))option.setAttribute('aria-checked',String(option.dataset.themeChoice===id))}for(const [id,name,colour,detail] of [['sand','Ivory','#f8f7f0','Warm stone · quiet light'],['teal','Deep teal','#101a19','Evergreen · soft glass'],['jet','Jet Black','#000000','Pure black · champagne'],['obsidian','Obsidian','#151617','Smoked graphite · warm porcelain']]){const b=button('',()=>choose(id),'theme-option');b.dataset.themeChoice=id;b.setAttribute('role','radio');b.setAttribute('aria-checked',String(current()===id));const swatch=element('span','theme-swatch');swatch.style.setProperty('--swatch',colour);const copy=element('span');copy.append(element('strong','',name),element('small','',detail));b.append(swatch,copy);choices.append(b)}root.append(choices)}
function account(){const root=showDialog(state.home?.user.name||'Your account.',state.home?(admin()?'Home administrator':'Home member'):'Sign in to your home.');if(window.__VA_NATIVE__)root.append(button('Server connections',()=>window.__VA_NATIVE__.call('app.settings')));if(state.home)root.append(button('Edit my dashboard',manageDashboard),button('Change my password',changeOwnPassword));root.append(button('Sign out',()=>client.signout()))}
async function connection(){state.home=null;state.entities.clear();clearInterval(state.timer);render();const root=showDialog('Welcome home.','Sign in with your home account. Your password stays between this device and your home server.');const form=element('div');root.append(form);if(!window.__VA_NATIVE__){const remember=field('Remember this device','','checkbox');remember.input.checked=client.rememberDevice;remember.input.onchange=()=>client.rememberDevice=remember.input.checked;root.append(remember.wrap)}const start=button('Sign in',async()=>{start.disabled=true;try{const setup=await StudioOnboarding.probe(client);if(setup?.needsOwner){const owner=showDialog('A home that’s yours.','Create the first owner for this new VAutomate home. Existing homes keep their accounts.');const body=element('div');owner.append(body);StudioOnboarding.render(client,body,dialogError);return}await loginStep(await client.beginLogin(),form)}catch(error){dialogError(error);start.disabled=false}},'primary');form.append(start);root.append(element('p','caption',window.__VA_NATIVE__?'Your sign-in is remembered in encrypted app storage.':'Keep Remember this device enabled on your own device. Turn it off on shared devices; sign-in then lasts for this tab. Sign out to forget this home account.'))}
async function loginStep(step,root){root.replaceChildren();if(step.type==='create_entry'){await client.finish(step.result);return}if(step.type!=='form')throw Error('This sign-in method needs installer assistance.');const form=element('form');for(const schema of step.data_schema||[]){const f=field(schema.name==='username'?'Username':schema.name==='password'?'Password':schema.name==='code'?'Verification code':schema.name,'',schema.name==='password'?'password':'text');f.input.name=schema.name;f.input.required=schema.required!==false;f.input.autocomplete=schema.name==='password'?'current-password':schema.name==='username'?'username':'one-time-code';if(schema.name==='code')f.input.inputMode='numeric';form.append(f.wrap)}const submit=element('button','primary',step.step_id==='mfa'?'Verify':'Continue');submit.type='submit';form.append(submit);form.onsubmit=async event=>{event.preventDefault();submit.disabled=true;const data=Object.fromEntries(new FormData(form));data.client_id=client.clientId;for(const input of form.querySelectorAll('input[type=password],input[name=code]'))input.value='';try{await loginStep(await client.auth('/auth/login_flow/'+encodeURIComponent(step.flow_id),data),root)}catch(error){dialogError(error);submit.disabled=false}};root.append(form);if(Object.keys(step.errors||{}).length)$('#dialog-error').textContent='Those details were not accepted. Please try again.'}
function setupNavigation(){const media=matchMedia('(max-width:760px)');try{if(!media.matches&&localStorage.getItem('vautomate-studio-commercial:sidebar')==='compact')document.body.classList.add('sidebar-compact')}catch{}$('#menu-toggle').append(icon('menu'));$('#menu-toggle').onclick=()=>{if(media.matches){const open=document.body.classList.toggle('sidebar-open');$('#scrim').hidden=!open;$('#menu-toggle').setAttribute('aria-expanded',String(open))}else{document.body.classList.toggle('sidebar-compact');try{localStorage.setItem('vautomate-studio-commercial:sidebar',document.body.classList.contains('sidebar-compact')?'compact':'expanded')}catch{}$('#menu-toggle').setAttribute('aria-expanded',String(!document.body.classList.contains('sidebar-compact')))}};$('#scrim').onclick=()=>{document.body.classList.remove('sidebar-open');$('#scrim').hidden=true};$('#appearance').onclick=appearance;$('#account-button').onclick=account;$('#signout').onclick=()=>client.signout();$('#close-dialog').onclick=closeDialog;$('#dialog').addEventListener('close',()=>{clearInterval(state.dialogTimer);state.dialogTimer=null;for(const input of $('#dialog').querySelectorAll('input[type=password],input[name=code]'))input.value=''});$('#dialog').addEventListener('cancel',event=>{clearPasswords();if(state.wizard&&state.dirty){event.preventDefault();closeDialog()}});window.addEventListener('hashchange',readRoute);window.addEventListener('scroll',()=>document.body.classList.toggle('scrolled',window.scrollY>45),{passive:true});document.addEventListener('keydown',spatialNavigation)}
function spatialNavigation(event){if(!document.body.classList.contains('tv')||!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(event.key))return;const active=document.activeElement;if(['INPUT','SELECT','TEXTAREA'].includes(active?.tagName))return;const root=$('#dialog').open?$('#dialog'):document.body;const nodes=[...root.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),[tabindex="0"]')].filter(n=>n.getClientRects().length&&getComputedStyle(n).visibility!=='hidden');const from=active?.getBoundingClientRect();if(!from||active===document.body){nodes[0]?.focus();event.preventDefault();return}const cx=from.x+from.width/2,cy=from.y+from.height/2,dx=event.key==='ArrowRight'?1:event.key==='ArrowLeft'?-1:0,dy=event.key==='ArrowDown'?1:event.key==='ArrowUp'?-1:0;let best=null,score=Infinity;for(const node of nodes){if(node===active)continue;const r=node.getBoundingClientRect(),x=r.x+r.width/2-cx,y=r.y+r.height/2-cy,forward=x*dx+y*dy;if(forward<4)continue;const cross=Math.abs(dx?y:x),cost=forward+cross*3;if(cost<score){best=node;score=cost}}if(best){event.preventDefault();best.focus({preventScroll:true});best.scrollIntoView({block:'nearest',inline:'nearest'})}else if(dy){event.preventDefault();window.scrollBy({top:dy*window.innerHeight*.65,behavior:'smooth'})}}
window.connection=connection;window.restoreRememberedSession=()=>client.restore();window.StudioApp={state,client,render,readRoute,runCommand,updateLive,bootstrap,openSetup};
client.onstatus=setConnection;client.onready=bootstrap;client.onlogin=connection;
try{const theme=localStorage.getItem('vautomate-studio-commercial:theme');if(['obsidian','jet','sand','teal'].includes(theme))document.body.dataset.theme=theme}catch{}
if(/Android TV|GoogleTV|SMART-TV|AFT/.test(navigator.userAgent))document.body.classList.add('tv');
setupNavigation();readRoute();
setTimeout(()=>{const arrival=$('#arrival');arrival.style.opacity='0';arrival.style.pointerEvents='none';setTimeout(()=>arrival.remove(),600)},matchMedia('(prefers-reduced-motion:reduce)').matches?150:3300);
if(window.STUDIO_DEMO_CLIENT){client.connected=true;setConnection('Showroom',true);bootstrap()}else if(!new URLSearchParams(location.search).has('native'))client.restore();

async function suggestRooms(){const wizard=state.wizard;if(!wizard||wizard.layout.rooms.length)return;try{const proposal=await client.request('commissioning/propose');if(state.wizard!==wizard)return;wizard.layout.rooms=proposal.layout.rooms.map(room=>({...room,entities:room.entities.filter(id=>state.discovery.entities.some(s=>s.entity_id===id&&StudioPresentation.everyday(s,state.discovery.registry?.find(r=>r.entity_id===id))))}));saveDraft();drawSetup();toast(proposal.layout.rooms.length?'Suggested rooms are ready to review. Nothing has been published.':'No existing room assignments found. Add rooms and choose devices below.')}catch(error){dialogError(error)}}
async function installationStatus(){if(!admin())return;const root=showDialog('Ready for your home.','A clear view of setup, health and remaining commissioning checks.');try{const report=await client.request('commissioning/status');root.append(element('p','caption','Installation '+report.installation_id));for(const check of report.checks){const row=element('div','settings-row');row.append(element('strong','',check.label),element('span','pill',check.status.replaceAll('_',' ')));root.append(row)}root.append(element('p','caption','This evaluation has not been certified for customer deployment. Device pairing, recovery and physical checks still need validation.'),button('Save installation record',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),link=element('a');link.href=url;link.download='VAutomate-installation-'+report.installation_id+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)},'primary'),element('p','caption','The record contains versions, counts and check results. It contains no account credentials, device names, addresses or location.'))}catch(error){dialogError(error)}}

async function openRecovery(){
 if(!admin())return;
 const root=showDialog('Backups & recovery.','Keep a separate copy of your home and its recovery password somewhere safe.'),epoch=state.dialogEpoch;
 try{
  const report=await client.request('backups/status');if(state.dialogEpoch!==epoch||!$('#dialog').open)return;
  const names={idle:'Ready',create_backup:'Creating your backup',restore_backup:'Restoring your home',receive_backup:'Receiving a backup',blocked:'Waiting for your home to start'};
  root.append(element('p','pill',names[report.state]||'Check recovery status'));
  if(report.storage_attention)root.append(element('p','dialog-error','Local backup storage needs attention. Available copies may be incomplete.'));
  if(report.last_outcome==='failed')root.append(element('p','dialog-error','The last recovery operation did not finish. Check your saved copies before trying a new request.'));
  const controls=element('div','device-actions'),create=button('Create encrypted backup',()=>createBackupReview(),'primary');create.disabled=report.state!=='idle'||!report.can_create;const load=button('Import saved copy',importBackupReview,'quiet');load.disabled=report.state!=='idle'||!report.can_create;controls.append(create,load,button('Refresh status',openRecovery));root.append(controls,element('p','caption','A copy saved only on this server is not independent protection. Downloads keep their encryption.'));
  if(!report.backups.length)root.append(element('p','','No local backups are available yet.'));
  for(const item of report.backups){const box=element('section','panel'),actions=element('div','device-actions');box.append(element('h3','',item.name),element('p','caption',new Date(item.date).toLocaleString()+' · '+formatBytes(item.size)+' · '+(item.protected?'Encrypted':'Unencrypted')));if(item.complete===false)box.append(element('p','dialog-error','Some parts were not saved. Review this copy carefully.'));const save=button('Save a separate copy',async()=>{save.disabled=true;try{const url=await client.backupDownload(item.backup_id);if(window.__VA_NATIVE__)await window.__VA_NATIVE__.call('download.home',{backup_id:item.backup_id});else{const link=element('a');link.href=url;link.download='VAutomate-backup-'+item.backup_id+'.tar';document.body.append(link);link.click();link.remove()}toast('Choose a safe location for your backup. Keep its password separately.')}catch(error){dialogError(error)}finally{save.disabled=false}});actions.append(save);if(item.home_included){const restore=button('Review restore',()=>restoreBackupReview(item.backup_id),'quiet');restore.disabled=report.state!=='idle';actions.append(restore)}box.append(actions);root.append(box)}
 }catch(error){dialogError(error)}
}
function formatBytes(size){return size>=1073741824?(size/1073741824).toFixed(1)+' GB':size>=1048576?(size/1048576).toFixed(1)+' MB':Math.ceil(size/1024)+' KB'}
async function createBackupReview(){
 const root=showDialog('Create a protected copy.','Your home, history and installed apps are included where supported. Nothing is changed in your rooms.');
 const name=field('Backup name','VAutomate home backup');root.append(name.wrap);const next=button('Review backup',async()=>{next.disabled=true;try{const review=await client.request('backups/preview',{kind:'create',name:name.input.value});drawBackupApproval(review)}catch(error){dialogError(error);next.disabled=false}},'primary');root.append(next);
}
async function restoreBackupReview(identity){try{drawBackupApproval(await client.request('backups/preview',{kind:'restore',backup_id:identity}))}catch(error){dialogError(error)}}
function drawBackupApproval(review){
 const restore=review.plan.kind==='restore',item=review.plan.backup;
 const root=showDialog(restore?'Restore this home?':'Keep the recovery password.',restore?'This replaces the current home with the selected saved copy. Controls and sign-in may disconnect while the server restarts.':'Choose a strong password. VAutomate will not keep it; losing it can make this backup unusable.');
 root.append(element('h3','',restore?item.name:review.plan.name));
 const includes=restore?item:review.plan.includes;root.append(element('p','caption',restore?new Date(item.date).toLocaleString()+' · Home configuration'+(item.database_included?', history':'')+' · '+item.app_count+' saved apps':'Home configuration and history'+(includes.all_apps?', all installed apps and server folders':'. Server apps are not part of this installation')));
 if(restore&&item.complete===false)root.append(element('p','dialog-error','This copy has reported missing parts. Those parts cannot be recovered from it.'));
 if(restore)for(const app of item.apps||[])root.append(element('p','caption',app.name+(app.version?' · '+app.version:'')));
 const password=field(restore?'Backup recovery password':'Choose a recovery password','','password');password.input.autocomplete=restore?'off':'new-password';root.append(password.wrap);
 let repeat,typed,ack;
 if(restore){typed=field('Type RESTORE to confirm','');root.append(typed.wrap);ack=field('I have saved a current independent backup and understand this will replace my home','','checkbox')}else{repeat=field('Repeat recovery password','','password');repeat.input.autocomplete='new-password';root.append(repeat.wrap);ack=field('I will keep this password separately from the backup','','checkbox')}root.append(ack.wrap);
 const approve=button(restore?'Restore saved home':'Create encrypted backup',async()=>{approve.disabled=true;try{if(!restore&&password.input.value!==repeat.input.value)throw new StudioError('invalid_input','The two passwords need to match.');const result=await client.request('backups/approve',{approval_nonce:review.approval_nonce,password:password.input.value,...(restore?{confirmation:typed.input.value,independent_copy:ack.input.checked}:{password_saved:ack.input.checked})});password.input.value='';if(repeat)repeat.input.value='';if(result.error_code==='password_incorrect'){throw new StudioError('invalid_input','The recovery password was not accepted. Review this backup again to try another password.')}if(result.status==='check_required'){showDialog('Check recovery status.','The result could not be confirmed. This request will not be repeated automatically. Refresh recovery status before making another decision.').append(button('Check status',openRecovery,'primary'));return}if(restore)showDialog('Your restore was requested.','Your server may restart and sign-in may change to the account saved in the backup. VAutomate will reconnect when the home is ready.').append(button('Check status',openRecovery,'primary'));else{toast('Backup started. Wait for it to appear, then save a separate copy.');await openRecovery()}}catch(error){dialogError(error);approve.disabled=false}finally{password.input.value='';if(repeat)repeat.input.value=''}},'primary');root.append(approve,button('Back to saved copies',openRecovery,'quiet'));
}

function importBackupReview(){
 const root=showDialog('Import a saved copy.','Select your exported Home Assistant backup archive. Importing adds a saved copy; it does not restore or replace your home.');
 const file=field('Backup archive','','file');file.input.accept='.tar,application/x-tar';root.append(file.wrap);const note=element('p','caption');root.append(note);const upload=button('Import this copy',async()=>{upload.disabled=true;file.input.disabled=true;try{const result=await client.backupUpload(file.input.files[0]);if(result.restored!==false)throw new StudioError('home_error','Refresh recovery status to check this import.');toast('Saved copy imported. Review it before choosing to restore.');await openRecovery()}catch(error){dialogError(error);upload.disabled=false;file.input.disabled=false}},'primary');upload.disabled=true;file.input.onchange=()=>{const selected=file.input.files[0];upload.disabled=!selected;note.textContent=selected?selected.name+' · '+formatBytes(selected.size):''};root.append(upload,button('Back to saved copies',openRecovery,'quiet'));
}

async function openHousehold(){
 if(!admin())return;
 const root=showDialog('Household access.','Give each person their own sign-in. Your household shares the published home; access follows their role.'),epoch=state.dialogEpoch;
 try{const [me,report]=await Promise.all([client.request('accounts/me'),client.request('accounts/list')]);if(epoch!==state.dialogEpoch||!$('#dialog').open)return;root.append(button('Add a person',()=>householdEditor(),'primary'));
  for(const person of report.users){const card=element('section','panel'),actions=element('div','device-actions');card.append(element('h3','',person.name),element('p','caption',(person.owner?'Home owner':person.role==='viewer'?'View-only access':person.administrator?'Administrator':'Home member')+' · '+(person.active?'Active':'Access paused')+(person.local_only?' · At-home access only':'')));if(person.owner||person.id===me.id)card.append(element('p','caption',person.owner?'The owner account is protected from removal and role changes.':'This is your account. Use Your account to change your own password.'));else{actions.append(button('Edit access',()=>householdEditor(person)));if(me.owner&&person.password_supported)actions.append(button('Reset password',()=>householdReview({kind:'reset_password',user_id:person.id}),'quiet'));actions.append(button('Remove access',()=>householdReview({kind:'remove',user_id:person.id}),'quiet'))}card.append(actions);root.append(card)}
 }catch(error){dialogError(error)}
}
function householdEditor(person){
 const root=showDialog(person?'Edit household access.':'Welcome someone home.',person?'Changes to access will end this person’s existing sessions. They must sign in again.':'Choose member, view-only or administrator access. Administrators can change this home and manage other household accounts.');
 const name=field('Person’s name',person?.name||''),role=selectField('Household role',[['member','Home member · use home controls'],['viewer','View only · see the home'],['administrator','Administrator · manage this home']],person?.role||'member'),local=field('Allow sign-in only when at home','','checkbox');local.input.checked=person?.local_only||false;root.append(name.wrap,role.wrap,local.wrap);let username,active;
 if(!person){username=field('Choose a username','');username.input.autocomplete='off';root.append(username.wrap)}else{active=field('This person can sign in','','checkbox');active.input.checked=person.active;root.append(active.wrap);if(person.role==='custom')root.append(element('p','caption','This account uses custom access. Selecting a standard role will replace that custom access.'))}
 root.append(button('Review account',()=>householdReview(person?{kind:'update',user_id:person.id,name:name.input.value,role:role.input.value,local_only:local.input.checked,active:active.input.checked}:{kind:'create',name:name.input.value,username:username.input.value,role:role.input.value,local_only:local.input.checked}),'primary'),button('Back to household',openHousehold,'quiet'));
}
async function householdReview(payload){try{const review=await client.request('accounts/preview',payload);drawHouseholdApproval(review)}catch(error){dialogError(error)}}
function drawHouseholdApproval(review){
 const plan=review.plan,kind=plan.kind,creating=kind==='create',removing=kind==='remove',reset=kind==='reset_password';
 const root=showDialog(creating?'Add this person?':removing?'Remove this person?':reset?'Reset this password?':'Save this access?',removing?'Their sign-in and saved sessions will be removed. Your rooms and routines will stay in place.':'Confirm with your own current password. Passwords are never included in a household listing.');
 root.append(element('h3','',creating?plan.name:plan.user.name));if(creating)root.append(element('p','caption','Username: '+plan.username+' · '+plan.role.replaceAll('_',' ')));if(kind==='update')root.append(element('p','caption',plan.changes.name+' · '+plan.changes.role+' · '+(plan.changes.active?'Active':'Access paused')+(plan.changes.local_only?' · At home only':'')));
 const current=field('Your current password','','password');current.input.autocomplete='current-password';root.append(current.wrap);let fresh,repeat,typed;
 if(creating||reset){fresh=field('New account password','','password');repeat=field('Repeat new account password','','password');fresh.input.autocomplete='new-password';repeat.input.autocomplete='new-password';root.append(fresh.wrap,repeat.wrap,element('p','caption','Share the sign-in privately. This person can change their password from Your account.'))}
 if(removing){typed=field('Type REMOVE to confirm','');root.append(typed.wrap)}
 const save=button(creating?'Add person':removing?'Remove this account':reset?'Reset password':'Save access',async()=>{save.disabled=true;try{if(fresh&&fresh.input.value!==repeat.input.value)throw new StudioError('invalid_input','The two new passwords need to match.');const result=await client.request('accounts/approve',{approval_nonce:review.approval_nonce,current_password:current.input.value,...(fresh?{new_password:fresh.input.value}:{}),...(typed?{confirmation:typed.input.value}:{})});if(result.status!=='saved'){showDialog('Check household access.','The result could not be confirmed. Nothing will be retried automatically. Refresh the household list before making another decision.').append(button('Check household',openHousehold,'primary'));return}toast(creating?'Person added. Share their sign-in privately.':removing?'This person’s access was removed.':'Account change saved. Existing sessions have ended.');await openHousehold()}catch(error){dialogError(error);save.disabled=false}finally{current.input.value='';if(fresh){fresh.input.value='';repeat.input.value=''}}},'primary');root.append(save,button('Back to household',openHousehold,'quiet'));
}
async function changeOwnPassword(){
 const root=showDialog('A password that’s yours.','Choose a strong new password. Your existing sessions will end, and you will sign in again on your devices.');
 const current=field('Current password','','password'),fresh=field('New password','','password'),repeat=field('Repeat new password','','password');current.input.autocomplete='current-password';fresh.input.autocomplete='new-password';repeat.input.autocomplete='new-password';root.append(current.wrap,fresh.wrap,repeat.wrap);
 const save=button('Change password & sign out',async()=>{save.disabled=true;try{if(fresh.input.value!==repeat.input.value)throw new StudioError('invalid_input','The two new passwords need to match.');await client.request('accounts/password',{current_password:current.input.value,new_password:fresh.input.value});await client.signout();toast('Password changed. Sign in again with your new password.')}catch(error){dialogError(error);save.disabled=false}finally{current.input.value='';fresh.input.value='';repeat.input.value=''}},'primary');root.append(save);
}


// Pairing is deliberate and bounded. Polling updates existing nodes, preserving remote focus.
function zigbeeSystem(controller){return ({zha:'ZHA',zigbee2mqtt:'Zigbee2MQTT'})[controller?.kind]||'Zigbee'}
function zigbeeStatusCard(controller){const card=element('section','panel zigbee-network');const title=element('div','zigbee-network-title');title.append(icon('routines'),element('h3','',zigbeeSystem(controller)));card.append(title,element('span','pill',controller.online?'Connected':'Not connected'),element('p','caption',controller.online?'Your coordinator is ready to add devices.':'Check coordinator power and its USB or network connection.'));return card}
async function openZigbee(){
 if(!admin())return;const root=showDialog('Zigbee.','Your network, coordinator and device setup in one place.'),epoch=state.dialogEpoch;
 root.append(element('p','caption','Checking your Zigbee connection…'));
 try{const [networks,report]=await Promise.all([client.request('pairing/status'),client.request('integrations/status')]);if(epoch!==state.dialogEpoch)return;integrationReport=report;root.lastChild.remove();
  if(networks.controllers.length){for(const controller of networks.controllers)root.append(zigbeeStatusCard(controller));const pair=button(networks.session&&networks.session.phase!=='closed'?'Continue adding a device':'Add a Zigbee device',()=>openPairing(),'primary');root.append(pair);if(!networks.controllers.some(c=>c.online))root.append(element('p','caption','Your network is configured but offline. Check its connection before pairing.'));}
  else{const configured=report.integrations.some(i=>i.domain==='zha')||report.apps.some(a=>a.id?.includes('zigbee2mqtt'));root.append(empty(configured?'Your Zigbee connection needs attention.':'Connect your coordinator once.',configured?'A Zigbee installation exists, but no ready network was reported. Check its connection; adding another coordinator will not repair it.':'A coordinator connects your home to Zigbee lights, curtains and sensors. After setup, use Add device for everyday pairing.',button(configured?'Check connection':'Set up coordinator',()=>configured?manageIntegrations():openCoordinatorWizard(),'primary')));}
  for(const setup of report.setups||[])if(['zha','zigbee2mqtt'].includes(setup.kind))root.append(button('Continue '+(setup.kind==='zha'?'ZHA':'Zigbee2MQTT')+' setup',()=>drawIntegrationSetup(setup),'primary'));
  const details=element('details','zigbee-details'),summary=element('summary','','Coordinator settings');details.append(summary,element('p','caption','Coordinator setup belongs here. Use one Zigbee system per adapter. Existing networks are protected; changing systems needs a migration review.'));
  const active=networks.controllers.map(zigbeeSystem);details.append(element('p','caption',active.length?'Configured system: '+active.join(' · '):'No active Zigbee network'));
  for(const entry of report.integrations.filter(i=>i.domain==='zha'))details.append(element('p','caption','ZHA · '+entry.state.replaceAll('_',' ')));
  for(const app of report.apps.filter(a=>a.id?.includes('zigbee2mqtt')))details.append(element('p','caption','Zigbee2MQTT app · '+(app.state||'Installed')));
  if(!networks.controllers.length&&!report.integrations.some(i=>i.domain==='zha'))details.append(button('Set up coordinator',()=>openCoordinatorWizard(),'quiet'));
  details.append(button('Refresh connection',openZigbee,'quiet'));root.append(details);
 }catch(error){if(epoch===state.dialogEpoch){dialogError(error);root.append(button('Try again',openZigbee,'primary'))}}
}
async function openPairing(fresh=false){
 if(!admin())return;
 const root=showDialog('Add a Zigbee device.','Choose a room. Put your device in pairing mode, then start the 60-second search.'),epoch=state.dialogEpoch;
 try{
  const report=await client.request('pairing/status');if(epoch!==state.dialogEpoch||!$('#dialog').open)return;
  if(report.session&&!(fresh===true&&report.session.phase==='closed')){const controller=report.controllers.find(c=>c.id===report.session.controller_id);if(controller)root.append(zigbeeStatusCard(controller));drawPairingSession(root,report,epoch);return}
  const networks=report.controllers.filter(c=>c.online);
  if(!networks.length){root.append(empty('Zigbee is not ready yet.','Check the coordinator connection before adding devices.',button('Open Zigbee settings',openZigbee,'primary')));return}
  if(!state.home.layout.rooms.length){root.append(element('p','caption','Create a room first so your new device has a place.'),button('Create a room',()=>roomEditor(null),'primary'));return}
  const network=selectField('Zigbee network',networks.map(c=>[c.id,zigbeeSystem(c)+' · '+c.name])),room=selectField('Room',state.home.layout.rooms.map(r=>[r.id,r.name]));
  if(networks.length===1)root.append(zigbeeStatusCard(networks[0]));else root.append(network.wrap);
  root.append(room.wrap);const steps=element('ol','pairing-instructions');for(const text of ['Keep the new device near your coordinator.','Follow the device’s instructions to enter pairing mode.','Start searching. Your device will appear here when connected.'])steps.append(element('li','',text));root.append(steps);
  const ready=field('My device is ready to pair','','checkbox');root.append(ready.wrap);
  const start=button('Start pairing',async()=>{start.disabled=true;ready.input.disabled=true;room.input.disabled=network.input.disabled=true;try{const review=await client.request('pairing/preview',{controller_id:network.input.value,room_id:room.input.value});if(epoch!==state.dialogEpoch)return;await client.request('pairing/begin',{approval_nonce:review.approval_nonce,ready:true});if(epoch===state.dialogEpoch)await openPairing();else toast('Device search started. It ends automatically after 60 seconds.')}catch(error){if(epoch===state.dialogEpoch){dialogError(error);root.append(button('Check pairing status',()=>openPairing(),'primary'))}}},'primary');start.disabled=true;ready.input.onchange=()=>start.disabled=!ready.input.checked||!report.can_start;root.append(start);if(!report.can_start)root.append(element('p','caption','Pairing is disabled in read-only evaluation. Your installer must enable commissioning controls.'));
 }catch(error){if(epoch===state.dialogEpoch){dialogError(error);root.append(button('Try again',()=>openPairing(),'primary'))}}
}
function pairingReview(review){
 const root=showDialog('Ready to connect?','Your '+review.plan.room_name+' device will be discovered on '+review.plan.controller_name+'. Pairing lasts at most 60 seconds. No controls are operated.'),epoch=state.dialogEpoch;
 const ready=field('My device is ready to pair','','checkbox');root.append(ready.wrap);
 const start=button('Start pairing',async()=>{start.disabled=true;ready.input.disabled=true;try{await client.request('pairing/begin',{approval_nonce:review.approval_nonce,ready:ready.input.checked});if(epoch===state.dialogEpoch)await openPairing();else toast('Check Add a device for pairing status. The network closes automatically after its bounded window.')}catch(error){if(epoch===state.dialogEpoch){dialogError(error);root.append(button('Check pairing status',openPairing,'primary'))}}},'primary');start.disabled=true;ready.input.onchange=()=>start.disabled=!ready.input.checked;root.append(start,button('Back',openPairing,'quiet'));
}
function drawPairingSession(root,initial,epoch){
 const summary=element('p','pairing-summary'),networkNote=element('p','caption'),list=element('div','pairing-devices'),rows=new Map();let busy=false,current=initial.session;
 const stop=button('Stop pairing',async()=>{stop.disabled=true;try{const result=await client.request('pairing/cancel',{session_id:current.id});if(epoch!==state.dialogEpoch)return;if(result.status!=='closed')throw new StudioError('check_required','The network did not confirm closure. Wait for its 60-second window to expire before checking again.');await poll()}catch(error){if(epoch===state.dialogEpoch){dialogError(error);stop.disabled=false}}},'quiet');
 const again=button('Add another device',()=>openPairing(true),'primary');again.hidden=true;root.append(summary,networkNote,list,stop,again);
 function update(report){
  current=report.session;if(!current){summary.textContent='Pairing status changed. Check again before starting.';return}
  const phase=current.phase;
  summary.textContent=phase==='listening'?'Looking for your device · '+current.seconds_remaining+' seconds':phase==='closed'?'Pairing is closed. You can still add discovered controls to a room.':phase==='window_finished'?'The search has ended. Finish this attempt to add another device.':'The previous attempt needs closing before you can add another device.';
  networkNote.textContent=current.network_attention?'The network is unavailable. No pairing request will be retried automatically.':'New devices appear below when setup finishes. Closing this view leaves only the original bounded window running.';
  stop.textContent=['check_required','window_finished'].includes(phase)?'Finish previous attempt':'Stop pairing';stop.hidden=phase==='closed';stop.disabled=false;again.hidden=phase!=='closed';const seen=new Set();
  for(const device of current.devices){
   seen.add(device.id);let row=rows.get(device.id);
   if(!row){const box=element('section','panel'),title=element('h3','',device.name),status=element('p','caption'),choices=element('div'),room=selectField('Place '+device.name+' in',state.home.layout.rooms.map(r=>[r.id,r.name]),current.room_id),add=button('Add to room',async()=>{add.disabled=true;add.dataset.pending='true';try{const entities=[...choices.querySelectorAll('input:checked')].map(i=>i.value);const result=await client.request('pairing/assign',{session_id:current.id,device_id:device.id,room_id:room.input.value,entities,revision:state.home.revision});if(epoch!==state.dialogEpoch)return;state.home.revision=result.revision;state.home.layout=result.layout;const selected=state.home.layout.rooms.find(r=>r.id===room.input.value);status.textContent='Added to '+selected.name+'.';toast('Device controls added to '+selected.name+'.');await refreshSnapshot()}catch(error){if(epoch===state.dialogEpoch)dialogError(error)}finally{delete add.dataset.pending;add.disabled=false}},'primary');box.append(title,status,choices,room.wrap,add);list.append(box);row={box,status,choices,room,add,entityIds:new Set()};rows.set(device.id,row)}
   row.box.hidden=false;const assigned=device.entities.length>0&&device.entities.every(e=>state.home.layout.rooms.some(r=>r.entities.includes(e.entity_id)));
   row.status.textContent=assigned?'Added to your home.':device.stage==='ready'?'Ready. Choose the controls and readings to show.':device.stage==='failed'?'Setup did not finish. Check your device’s pairing instructions.':'Connecting securely. Waiting for its controls.';
   for(const entity of device.entities){if(row.entityIds.has(entity.entity_id))continue;row.entityIds.add(entity.entity_id);const choice=field(entity.name,'','checkbox');choice.input.value=entity.entity_id;choice.input.checked=true;row.choices.append(choice.wrap)}
   row.add.disabled=device.stage!=='ready'||assigned||row.add.dataset.pending==='true';row.choices.hidden=device.stage!=='ready'||assigned;row.room.wrap.hidden=device.stage!=='ready'||assigned;row.add.hidden=assigned;
  }
  for(const [id,row] of rows)row.box.hidden=!seen.has(id);
  if(!rows.size)networkNote.textContent+=' No new devices yet.';
 }
 async function poll(){if(busy||epoch!==state.dialogEpoch||!$('#dialog').open)return;busy=true;try{const report=await client.request('pairing/status');if(epoch===state.dialogEpoch&&$('#dialog').open){$('#dialog-error').textContent='';update(report)}}catch(error){if(epoch===state.dialogEpoch)dialogError(error)}finally{busy=false}}
 update(initial);state.dialogTimer=setInterval(poll,2500);
}


async function openReplacement(){
 if(!admin())return;
 const root=showDialog('Replace a device.','Pair the new device first, then move the old device’s VAutomate controls and rules here. This does not remove a device from its radio network.'),epoch=state.dialogEpoch;
 try{
  const [report,discovery]=await Promise.all([client.request('replacements/status'),client.request('discover')]);if(epoch!==state.dialogEpoch)return;
  root.append(element('p','caption',report.scope));
  const source=selectField('Old control',[["","Choose the old control"],...report.entities.map(e=>[e.entity_id,e.name+(e.missing?' · missing':'' )])]),target=selectField('New control',[["","Choose a replacement"]]);
  const known=new Set(report.entities.map(e=>e.entity_id));
  source.input.onchange=()=>{target.input.replaceChildren();for(const [value,label] of [["","Choose a replacement"],...discovery.entities.filter(e=>!known.has(e.entity_id)&&domain(e.entity_id)===domain(source.input.value)&&online(e)).map(e=>[e.entity_id,entityName(e)])]){const opt=element('option','',label);opt.value=value;target.input.append(opt)}review.disabled=true};
  const review=button('Review replacement',async()=>{review.disabled=true;try{const plan=await client.request('replacements/preview',{replacements:[{from:source.input.value,to:target.input.value}],revision:state.home.revision});if(epoch===state.dialogEpoch)replacementReview(plan)}catch(error){if(epoch===state.dialogEpoch){dialogError(error);review.disabled=false}}},'primary');review.disabled=true;target.input.onchange=()=>review.disabled=!source.input.value||!target.input.value;root.append(source.wrap,target.wrap,review,element('p','caption','If no replacement appears, finish pairing and discovery without adding it to a room. Use a matching device type and reading unit.'));
 }catch(error){if(epoch===state.dialogEpoch)dialogError(error)}
}
function replacementReview(plan){
 const root=showDialog('Review the replacement.','Affected schedules and automations will stay paused. Test the new device, then deliberately review and enable each rule.'),epoch=state.dialogEpoch;
 if(plan.missing_original)root.append(element('p','caption','The original device is missing. Its previous reading type and unit cannot be verified; check them before proceeding.'));
 for(const [kind,title] of [['rooms','Rooms'],['home_buttons','Home buttons'],['dashboard_cards','Dashboard cards'],['schedules','Schedules · will pause'],['automations','Automations · will pause']]){root.append(element('h3','',title));const items=plan.changes[kind]||[];root.append(element('p','caption',items.length?items.map(i=>typeof i==='string'?i:i.name).join(', '):'None affected.'))}
 const physical=field('I checked that this replacement is suitable','','checkbox'),scope=field('I will review external scenes and automations separately','','checkbox');root.append(physical.wrap,scope.wrap);
 const approve=button('Replace and pause affected rules',async()=>{approve.disabled=true;physical.input.disabled=true;scope.input.disabled=true;try{await client.request('replacements/approve',{approval_nonce:plan.approval_nonce,confirmed:physical.input.checked,external_scope_ack:scope.input.checked});if(epoch!==state.dialogEpoch)return;await bootstrap();showDialog('Replacement saved.','Your shared VAutomate home now uses the replacement. Affected schedules and automations are paused. Test controls and review the rules before enabling them.')}catch(error){if(epoch===state.dialogEpoch){dialogError(error);root.append(button('Check current home',async()=>{await bootstrap();navigate('care')},'quiet'))}}},'primary');approve.disabled=true;physical.input.onchange=scope.input.onchange=()=>approve.disabled=!physical.input.checked||!scope.input.checked;root.append(approve,button('Back',openReplacement,'quiet'));
}


function renderManagement(page){
 if(!admin()){page.append(empty('Administrator access required.','Your home controls remain available.',button('Back home',()=>navigate('home'),'primary')));return}
 page.append(heading('Make this home yours.','A place for everything. Start with a room or connect something new.'));const start=element('section','panel management-start');const copy=element('div');copy.append(element('h2','','Something new for your home?'),element('p','caption','Connect it, give it a familiar name, then choose its room.'));start.append(copy,button('Add a device',addDeviceHub,'primary'));page.append(start);
 const grid=element('div','management-grid');for(const [title,copy,mark,action] of [
 ['Rooms','Create spaces, arrange them and choose their controls.','rooms',manageRooms],['Devices','Lights, fans, curtains, media and everyday controls.','switch',manageDevices],['Zigbee','See your active system, coordinator and connection status.','routines',openZigbee],['Device brands & apps','Connect supported cameras, media, Wi-Fi devices and other services.','switch',manageIntegrations],['Dashboard','Add, arrange and resize cards. Edit your home’s welcome and shortcuts.','home',manageDashboard],['Automations','Guided recipes and a visual builder for your own ideas.','routines',()=>navigate('routines')],['Household access','Give each person the right access to your home.','person',openHousehold],['Backups & recovery','Keep an independent copy and review recovery options.','history',openRecovery],['Remote access','Connect from anywhere with your own private Tailscale account.','care',openRemoteAccess],['System status','Connection, installation health and recent activity.','care',()=>navigate('care')]]){
  const card=button('',action,'panel management-card');card.append(icon(mark),element('h2','',title),element('p','caption',copy),element('span','management-arrow','Explore →'));grid.append(card)
 }page.append(grid);
}
async function saveManagedLayout(layout,revision){await client.request('layout/preview',{layout});await client.request('layout/publish',{layout,revision});window.VAutomateUI?.clearFields();await bootstrap()}
function manageRooms(){
 if(!admin())return;const root=showDialog('Your rooms.','Create a space, give it a familiar name and choose what belongs there.');root.append(button('Create a room',()=>roomEditor(null),'primary'));const list=element('div','management-list');root.append(list);
 if(!state.home.layout.rooms.length)list.append(element('p','caption','Your first room starts here. Add connected devices whenever you are ready.'));
 for(const room of state.home.layout.rooms){const row=element('div','settings-row'),open=button('',()=>roomEditor(room),'room-management-link');open.append(element('strong','',room.name),element('small','caption',room.entities.length+' controls & readings'));row.append(open,button('Edit room',()=>roomEditor(room),'quiet'));list.append(row)}
 root.append(button('Back to management',()=>{closeDialog();navigate('manage')},'quiet'));
}
async function roomEditor(original,restore=false){if(!admin())return;
 const draftKey=original?.id||'new',saved=window.VAutomateUI?.readModel('room',draftKey);
 const root=showDialog(original?'Edit '+original.name:'A new room.','Choose lights, fans, curtains and the things you use every day. Saved changes apply to your household.'),epoch=state.dialogEpoch,revision=state.home.revision,room=restore&&saved?structuredClone(saved):original?structuredClone(original):{id:uid(),name:'',entities:[]};const name=field('Room name',room.name);root.dataset.vaModelEditor='true';root.dataset.vaDraftKey='room:'+draftKey;window.VAutomateUI?.trackModel('room',draftKey,()=>({...room,name:name.input.value}));if(saved&&!restore)root.append(button('Restore room draft',()=>roomEditor(original,true),'quiet'));name.input.maxLength=80;const search=field('Find devices or readings'),types=selectField('Show',[["all","All controls & readings"],["light","Lights"],["switch","Switches"],["fan","Fans"],["cover","Curtains"],["sensor","Readings"],["binary_sensor","Presence & security sensors"],["media_player","Media"],["alarm_control_panel","Home security"]]);root.append(name.wrap,search.wrap,types.wrap);const list=element('div','entity-library');root.append(list);let discovery;
 try{discovery=await client.request('discover');if(epoch!==state.dialogEpoch)return}catch(error){dialogError(error);return}
 const registry=new Map(discovery.registry.map(e=>[e.entity_id,e]));let reveal=false;const selection=element('p','selection-summary');root.append(selection);const extra=field('Show system entities · administrator only','','checkbox');extra.input.onchange=()=>{reveal=extra.input.checked;draw()};root.append(extra.wrap);
 function draw(){selection.textContent=room.entities.length+' selected for this room';list.replaceChildren();const visible=discovery.entities.filter(e=>(reveal||StudioPresentation.everyday(e,registry.get(e.entity_id)))&&(!search.input.value||entityName(e).toLowerCase().includes(search.input.value.toLowerCase()))&&(types.input.value==='all'||domain(e.entity_id)===types.input.value));for(const entity of visible){const choice=field(entityName(entity),'','checkbox');choice.wrap.classList.add('entity-choice');choice.input.checked=room.entities.includes(entity.entity_id);choice.input.onchange=()=>{room.entities=choice.input.checked?[...new Set([...room.entities,entity.entity_id])]:room.entities.filter(i=>i!==entity.entity_id);selection.textContent=room.entities.length+' selected for this room'};choice.wrap.append(element('small','caption',deviceKind(entity)+' · '+labelState(entity)));list.append(choice.wrap)}if(!visible.length)list.append(element('p','caption','No matching devices are connected. Save this room, then use Add a device to connect hardware.'))}
 search.input.oninput=draw;types.input.onchange=draw;draw();
 const save=button('Save room',async()=>{save.disabled=true;try{room.name=name.input.value;const layout=structuredClone(state.home.layout);if(original)layout.rooms=layout.rooms.map(r=>r.id===room.id?room:r);else layout.rooms.push(room);await saveManagedLayout(layout,revision);window.VAutomateUI?.clearModel('room',draftKey);toast('Room saved for your household.');manageRooms()}catch(error){if(epoch===state.dialogEpoch)dialogError(error);save.disabled=false}},'primary');root.append(save,button('Add a device',addDeviceHub,'quiet'));
 if(original)root.append(button('Remove room',()=>{const confirmRoot=showDialog('Remove '+original.name+'?','Remove this room and its room-shortcut cards. Your connected devices are kept. Routines using this room must be reviewed first.'),confirm=button('Remove this room',async()=>{confirm.disabled=true;try{const layout=StudioPresentation.removeRoom(state.home.layout,original.id);await saveManagedLayout(layout,revision);window.VAutomateUI?.clearModel('room',original.id);toast('Room removed. Connected devices are kept.');manageRooms()}catch(error){dialogError(error);if(error.code==='references_in_use')confirmRoot.append(button('Review linked routines',()=>{closeDialog();navigate('routines')},'primary'));confirm.disabled=false}},'quiet');confirmRoot.append(confirm,button('Keep room',()=>roomEditor(original),'primary'))},'quiet'));
 root.append(button('Back to rooms',manageRooms,'quiet'));
}
function addDeviceHub(){if(!admin())return;const root=showDialog('Connect something new.','Bring a device into your home, then choose the room and controls to show.');root.append(button('Pair a Zigbee device',()=>openPairing(),'primary'),button('Choose an already connected device',manageDevices),button('Other device brands & apps',manageIntegrations,'quiet'))}
async function manageDevices(){if(!admin())return;
 if(!admin())return;const root=showDialog('Connected devices.','Find a control, give it a familiar name and choose its room.'),epoch=state.dialogEpoch;root.append(button('Connect a new device',addDeviceHub,'primary'));const search=field('Search connected devices'),system=field('Show system entities · administrator only','','checkbox');root.append(search.wrap,system.wrap);const list=element('div','management-list');root.append(list);
 try{const discovery=await client.request('discover');if(epoch!==state.dialogEpoch)return;const registry=new Map(discovery.registry.map(e=>[e.entity_id,e])),devices=new Map(discovery.devices.map(d=>[d.id,d]));const groups=new Map();for(const entity of discovery.entities){const entry=registry.get(entity.entity_id);if(entry?.disabled)continue;const identity=entry?.device_id||entity.entity_id,device=devices.get(entry?.device_id);if(!groups.has(identity))groups.set(identity,{name:device?.name||entityName(entity),device,entities:[]});groups.get(identity).entities.push(entity)}function draw(){list.replaceChildren();const visibleGroups=[...groups.values()].map(g=>({...g,entities:g.entities.filter(e=>system.input.checked||StudioPresentation.everyday(e,registry.get(e.entity_id)))})).filter(g=>g.entities.length);const matches=visibleGroups.filter(g=>(g.name+' '+g.entities.map(entityName).join(' ')).toLowerCase().includes(search.input.value.toLowerCase()));for(const group of matches){const row=button('',()=>{const details=showDialog(group.name,'Choose a control or reading to rename it or edit its room placement.');for(const entity of group.entities){const item=button('',()=>editConnectedEntity(entity,registry.get(entity.entity_id)),'settings-row connected-entity');item.append(icon(domain(entity.entity_id)),element('strong','',entityName(entity)),element('span','pill',labelState(entity)));details.append(item)}details.append(button('Back to devices',manageDevices,'quiet'))},'settings-row connected-entity');row.append(icon(domain(group.entities[0].entity_id)),element('strong','',group.name),element('span','caption',group.entities.length+' controls & readings'));list.append(row)}if(!matches.length)list.append(element('p','caption','No connected devices match. Set up your Zigbee connection or MQTT broker to discover hardware.'))}search.input.oninput=draw;system.input.onchange=draw;draw()}catch(error){dialogError(error)}
}
function editConnectedEntity(entity,registry){if(!admin())return;
 const root=showDialog(entityName(entity),'Edit its name or choose where this control appears.'),epoch=state.dialogEpoch,name=field('Control name',entityName(entity));name.input.maxLength=80;root.append(name.wrap);const rename=button('Save name',async()=>{rename.disabled=true;try{await client.request('registry/rename',{entity_id:entity.entity_id,name:name.input.value,expected_name:registry?.name||null});await bootstrap();toast('Control name saved.');manageDevices()}catch(error){if(epoch===state.dialogEpoch)dialogError(error);rename.disabled=false}},'primary');rename.disabled=!registry;root.append(rename);if(!registry)root.append(element('p','caption','This integration does not expose an editable name. Room placement is available below.'));
 const selected=new Set(state.home.layout.rooms.filter(r=>r.entities.includes(entity.entity_id)).map(r=>r.id));for(const room of state.home.layout.rooms){const choice=field(room.name,'','checkbox');choice.input.checked=selected.has(room.id);choice.input.onchange=()=>{if(choice.input.checked)selected.add(room.id);else selected.delete(room.id)};root.append(choice.wrap)}const revision=state.home.revision;
 root.append(button('Save room placement',async()=>{try{const layout=structuredClone(state.home.layout);for(const room of layout.rooms)room.entities=selected.has(room.id)?[...new Set([...room.entities,entity.entity_id])]:room.entities.filter(i=>i!==entity.entity_id);await saveManagedLayout(layout,revision);toast('Room placement saved.');manageDevices()}catch(error){dialogError(error)}},'primary'),button('Create a room',()=>roomEditor(null),'quiet'),button('Back to devices',manageDevices,'quiet'));
}
let integrationReport=null;
let coordinatorChoice=null;
/* COORDINATOR_ADDRESS_BEGIN */
function coordinatorAddress(host,port,kind){host=String(host||'').trim();const number=Number(port);if(!host||/[\s\/?#@]/.test(host)||!Number.isInteger(number)||number<1024||number>65535)throw Error('Enter the coordinator address and its serial port number, between 1024 and 65535.');if(host.includes(':')&&!host.startsWith('['))host='['+host+']';let url;try{url=new URL('http://'+host+':'+number)}catch{throw Error('Check the coordinator IP address or hostname.')}return (kind==='zigbee2mqtt'?'tcp':'socket')+'://'+url.host}
/* COORDINATOR_ADDRESS_END */
async function openCoordinatorWizard(preferred='zha',previous=null){
 if(!admin())return;
 const root=showDialog('Connect your Zigbee coordinator.','A coordinator connects your Zigbee lights, curtains and sensors to this home.'),epoch=state.dialogEpoch;
 try{const report=await client.request('integrations/status');if(epoch!==state.dialogEpoch)return;integrationReport=report;
 const current=previous||{kind:preferred,connection:'usb',port:report.serial_ports.length===1?report.serial_ports[0].value:'',history:'unknown',host:'',networkPort:'6638'};
 const progress=element('div','coordinator-progress');for(const text of ['1 · Connect adapter','2 · Review & detect','3 · Add devices'])progress.append(element('span','',text));root.append(progress);
 const connection=selectField('How is the coordinator connected?', [['usb','USB · plugged into this home server'],['network','Network · Ethernet or Wi-Fi adapter']],current.connection),system=selectField('Zigbee system',[['zha','ZHA · simplest setup'],['zigbee2mqtt','Zigbee2MQTT · MQTT-based setup']],current.kind),history=selectField('Has this coordinator been used before?',[['unknown','I’m not sure · protect any existing network'],['used','Yes · keep its existing network'],['unused','No · this is a new, unused coordinator']],current.history);
 root.append(system.wrap,element('p','caption','ZHA is the simplest choice for most homes. Zigbee2MQTT also needs MQTT. Use only one system with each coordinator.'),connection.wrap);
 const port=selectField('Detected USB adapter',[['','Choose an adapter'],...report.serial_ports.map(p=>[p.value,p.label])],current.port),host=field('Coordinator IP address or hostname',current.host),networkPort=field('Coordinator serial port',current.networkPort,'number');networkPort.input.min='1024';networkPort.input.max='65535';host.input.placeholder='coordinator.local';
 const emptyUsb=element('section','panel coordinator-empty');emptyUsb.append(element('strong','','No USB adapter detected in this server.'),element('p','caption','Plug it into the home server. For a virtual server, assign the USB device to that VM first. Then refresh this list.'),button('Refresh adapters',()=>openCoordinatorWizard(system.input.value,{kind:system.input.value,connection:connection.input.value,port:port.input.value,history:history.input.value,host:host.input.value,networkPort:networkPort.input.value}),'quiet'));
 const help=element('p','caption','You do not need to know the model for ZHA. Detection will identify supported radios after you approve it.'),notice=element('p','coordinator-notice');root.append(port.wrap,emptyUsb,host.wrap,networkPort.wrap,history.wrap,help,notice);
 const resume=(report.setups||[]).filter(s=>['zha','zigbee2mqtt'].includes(s.kind));for(const setup of resume)root.append(button('Resume current '+integrationName(setup.kind)+' setup',()=>drawIntegrationSetup(setup),'primary'));
 const next=button('Review connection',()=>{try{let target;if(connection.input.value==='usb'){if(!port.input.value){window.VAutomateUI?.fieldError(port.input,'Choose a detected adapter.');return}target=port.input.value}else target=coordinatorAddress(host.input.value,networkPort.input.value,system.input.value);coordinatorChoice={kind:system.input.value,connection:connection.input.value,port:target,history:history.input.value,serialSubmitted:false};integrationPreview(system.input.value,true)}catch(error){dialogError(error)}},'primary');root.append(next,button('Other connections',manageIntegrations,'quiet'));
 function update(){const usb=connection.input.value==='usb';port.wrap.hidden=!usb||!report.serial_ports.length;emptyUsb.hidden=!usb||!!report.serial_ports.length;host.wrap.hidden=networkPort.wrap.hidden=usb;const existing=report.integrations.some(i=>i.domain==='zha');const previouslyUsed=history.input.value!=='unused';notice.textContent=existing?'ZHA is already configured for this home. Pair devices with that network; replacing its coordinator needs a separate migration review.':system.input.value==='zigbee2mqtt'&&previouslyUsed?'A used or unknown coordinator needs a backup and migration review before starting Zigbee2MQTT. Choose ZHA to keep an existing network when one is found.':previouslyUsed?'Existing network protection is on. No erase or new-network option will be offered.':'A new network can be created only after you choose that step.';next.disabled=!!resume.length||existing||usb&&!report.serial_ports.length||system.input.value==='zigbee2mqtt'&&previouslyUsed}
 for(const input of [connection.input,system.input,history.input])input.onchange=update;update();
 if(report.integrations.some(i=>i.domain==='zha')||report.apps.some(a=>a.id?.includes('zigbee2mqtt')&&a.state==='started'))root.append(button('Add a Zigbee device',()=>openPairing(),'primary'));
 }catch(error){if(epoch===state.dialogEpoch){dialogError(error);root.append(button('Try again',()=>openCoordinatorWizard(preferred),'primary'))}}
}

function integrationName(kind){return integrationReport?.catalogue?.find(i=>i.id===kind)?.name||({zha:'ZHA',mqtt:'MQTT',zigbee2mqtt:'Zigbee2MQTT'})[kind]||kind}
async function manageIntegrations(){
 if(!admin())return;const root=showDialog('Device brands & apps.','Connect a supported brand or service. Manage your coordinator separately in Zigbee settings.'),epoch=state.dialogEpoch;
 try{const report=await client.request('integrations/status');if(epoch!==state.dialogEpoch)return;integrationReport=report;const quick=element('section','panel coordinator-start');quick.append(element('h3','','Your Zigbee network'),element('p','caption','See which system is active and manage its coordinator.'),button('Open Zigbee settings',openZigbee,'quiet'));root.append(quick);
  for(const entry of report.integrations){const row=element('div','settings-row');row.append(element('strong','',entry.name),element('span','pill',entry.state.replaceAll('_',' ')));root.append(row)}for(const app of report.apps){const row=element('div','settings-row');row.append(element('strong','',app.name),element('span','pill',app.state||'Installed'));root.append(row)}
  for(const setup of report.setups||[])root.append(button('Resume '+({zha:'ZHA',mqtt:'MQTT',zigbee2mqtt:'Zigbee2MQTT'})[setup.kind],()=>drawIntegrationSetup(setup),'primary'));
  const options=element('div','integration-options');for(const [kind,title,description] of (report.catalogue||[{id:'zha',name:'ZHA',description:'Connect a Zigbee coordinator.'},{id:'zigbee2mqtt',name:'Zigbee2MQTT',description:'Install and connect the bridge.'},{id:'mqtt',name:'MQTT connection',description:'Connect a broker.'}]).filter(i=>!['zha','zigbee2mqtt'].includes(i.id)).map(i=>[i.id,i.name,i.description])){const card=element('section','panel');card.append(element('h3','',title),element('p','caption',description),button('Set up '+title,()=>integrationPreview(kind),'primary'));options.append(card)}root.append(options);
  if(!report.serial_ports.length)root.append(element('p','caption','No USB coordinator is detected inside this HAOS installation. Connect one to the server, or use a supported LAN coordinator. An adapter attached to another home server cannot be shared by two Zigbee networks.'));
  root.append(button('Pair a connected Zigbee device',()=>openPairing(),'quiet'));
 }catch(error){dialogError(error)}
}
async function integrationPreview(kind,guided=false){
 if(['zha','zigbee2mqtt'].includes(kind)&&!guided)return openCoordinatorWizard(kind);
 try{const plan=await client.request('integrations/preview',{kind}),radio=['zha','zigbee2mqtt'].includes(kind),root=showDialog('Set up '+integrationName(kind)+'?',radio?'Review before detection. The adapter or serial connection may restart. This does not approve erasing an existing Zigbee network.':'Existing integrations are kept. Review this connection before continuing.');
 if(radio&&coordinatorChoice){const summary=element('div','coordinator-review');summary.append(element('strong','',coordinatorChoice.connection==='usb'?'Selected USB adapter':'Selected network coordinator'),element('p','caption',coordinatorChoice.history==='unused'?'New, unused coordinator':'Protect existing network settings'));root.append(summary)}
 if(plan.third_party_software)root.append(element('p','caption','Zigbee2MQTT installs software from its official repository and needs MQTT. Installation can take several minutes.'));
 const ready=field(radio?'Allow detection · the adapter or serial connection may restart':'I approve this setup and have an available coordinator or broker','','checkbox');root.append(ready.wrap);const start=button('Begin setup',async()=>{start.disabled=true;try{const result=await client.request('integrations/begin',{approval_nonce:plan.approval_nonce,confirmed:ready.input.checked,...(radio?{radio_detection_approved:ready.input.checked,coordinator_history:coordinatorChoice?.history||'unknown'}:{})});drawIntegrationSetup(result)}catch(error){dialogError(error);root.append(button('Check setup status',manageIntegrations,'primary'))}},'primary');start.disabled=true;ready.input.onchange=()=>start.disabled=!ready.input.checked;root.append(start,button('Back',()=>radio?openCoordinatorWizard(kind):manageIntegrations(),'quiet'))
 }catch(error){dialogError(error)}
}
function drawIntegrationSetup(setup){
 const names={zha:'ZHA',mqtt:'MQTT',zigbee2mqtt:'Zigbee2MQTT'},labels={device_path:'Coordinator connection',path:'Coordinator connection',port:setup.kind==='mqtt'?'Broker port':'Coordinator connection',broker:'Broker address',username:'Broker username',password:'Broker password',radio_type:'Coordinator radio type',adapter:'Coordinator type',baudrate:'Connection speed',flow_control:'Flow control',install_broker:'Also install the Mosquitto MQTT broker',software_approved:'I approve installing this third-party software',broker_mode:'MQTT connection',protocol:'MQTT version'};
 const root=showDialog(integrationName(setup.kind)+' setup.',setup.message||'Complete this step to connect your home. Credentials are sent only to this home server.'),epoch=state.dialogEpoch;
 const cancel=()=>{const b=button('Cancel setup',async()=>{b.disabled=true;try{await client.request('integrations/cancel',{session_id:setup.session_id});await manageIntegrations()}catch(error){dialogError(error);b.disabled=false}},'quiet');return b};
 if(setup.type==='complete'){coordinatorChoice=null;root.append(button('Add devices to a room',()=>openPairing(),'primary'),button('View connected devices',manageDevices),button('Create a room',()=>roomEditor(null),'quiet'),button('Connections',manageIntegrations,'quiet'));return}
 if(setup.type==='aborted'||setup.type==='check_required'){root.append(element('p','caption',setup.reason?setup.reason.replaceAll('_',' '):'The result needs checking. Nothing will be retried automatically.'),button('Check connections',manageIntegrations,'primary'),cancel());return}
 async function send(input){try{const result=await client.request('integrations/step',{session_id:setup.session_id,generation:setup.generation,input,request_id:uid()});if(epoch===state.dialogEpoch)drawIntegrationSetup(result)}catch(error){if(epoch===state.dialogEpoch){dialogError(error);root.append(button('Check setup status',manageIntegrations,'primary'))}}}
 const serialField=(setup.fields||[]).find(f=>['path','device_path'].includes(f.name)||f.selector?.serial_port!==undefined);
 if(setup.kind==='zha'&&setup.type==='form'&&setup.step==='choose_serial_port'&&coordinatorChoice?.kind==='zha'&&coordinatorChoice.port&&!coordinatorChoice.serialSubmitted&&serialField&&!Object.keys(setup.errors||{}).length){coordinatorChoice.serialSubmitted=true;root.append(element('p','caption','Identifying the selected coordinator. Its existing network will be kept. If this takes longer, check setup status rather than submitting again.'),button('Check setup progress',manageIntegrations,'quiet'));send({[serialField.name]:coordinatorChoice.port});return}
 if(setup.type==='menu'){for(const value of setup.options)root.append(button(({setup_strategy_advanced:'Choose network settings',reuse_settings:'Keep and use the coordinator’s existing network',form_initial_network:'Create a new network on this unused coordinator',manual_pick_radio_type:'Choose coordinator type',choose_serial_port:'Choose coordinator connection',broker:'Use an existing MQTT broker',addon:'Install or connect the managed MQTT broker'})[value]||value.replaceAll('_',' '),()=>send({next_step_id:value}),'primary'));root.append(cancel());return}
 if(setup.type==='working'){root.append(element('p','caption','Your home is still processing this setup. Nothing needs to be submitted again.'),button('Refresh setup status',manageIntegrations,'primary'));return}
 if(['progress','progress_done'].includes(setup.type)){root.append(element('p','caption','Your home is preparing this connection. Installation and connection checks may take a little time.'),button('Check progress',()=>send({_refresh:true}),'primary'),button('Connections & status',manageIntegrations),cancel());return}
 if(setup.type!=='form'){root.append(button('Check connections',manageIntegrations,'primary'),cancel());return}
 if(Object.keys(setup.errors||{}).length)root.append(element('p','dialog-error','Connection settings were not accepted: '+Object.values(setup.errors).map(v=>v.replaceAll('_',' ')).join(', ')));
 const readers=[],passwords=[];let unsupported=false;
 function formFields(fields,target,readers){for(const f of fields||[]){const label=labels[f.name]||f.name.replaceAll('_',' '),selector=f.selector||{},selection=selector.select,section=f.schema||f.data_schema;if(Array.isArray(section)){const details=element('details','rule-group');details.append(element('summary','',label));const nested=[];formFields(section,details,nested);readers.push(()=>[f.name,Object.fromEntries(nested.map(read=>read()))]);target.append(details);continue}
   let fieldView,read;
   const options=f.options||selection?.options;
   if(selector.serial_port!==undefined||setup.kind==='zigbee2mqtt'&&f.name==='port'){
    const available=integrationReport?.serial_ports||[],selected=f.default||coordinatorChoice?.port||'',manual=field('Network or other coordinator address',selected);manual.input.placeholder=setup.kind==='zha'?'socket://coordinator:6638':'tcp://coordinator:6638';
    fieldView=selectField(label,[...available.map(p=>[p.value,p.label]),['__manual__','Network or other connection']],available.some(p=>p.value===selected)?selected:'__manual__');
    const update=()=>manual.wrap.hidden=fieldView.input.value!=='__manual__';fieldView.input.onchange=update;update();target.append(fieldView.wrap,manual.wrap);fieldView.input.name=f.name;readers.push(()=>[f.name,fieldView.input.value==='__manual__'?manual.input.value.trim():fieldView.input.value]);continue;
   }
   if(options){const entries=options.map(v=>Array.isArray(v)?v:typeof v==='object'?[v.value,v.label]:[v,v]);fieldView=selectField(label,entries.map(([v,l])=>[String(v),String(l)]),f.default!==undefined?String(f.default):undefined);if(['radio_type','adapter'].includes(f.name)){const placeholder=element('option','','Choose the radio family');placeholder.value='';fieldView.input.prepend(placeholder);fieldView.input.value='';fieldView.input.required=true}read=()=>entries.find(v=>String(v[0])===fieldView.input.value)?.[0]??fieldView.input.value}
   else if(f.type==='boolean'||selector.boolean!==undefined){fieldView=field(label,'','checkbox');fieldView.input.checked=f.default===true;read=()=>fieldView.input.checked}
   else if(selector.serial_port!==undefined&&integrationReport?.serial_ports.length){fieldView=selectField(label,integrationReport.serial_ports.map(v=>[v.value,v.label]),f.default);read=()=>fieldView.input.value}
   else if(['string','integer','float','number'].includes(f.type)||selector.text!==undefined||selector.number!==undefined||selector.serial_port!==undefined){const secret=/password|secret|token|psk|key/i.test(f.name)||selector.text?.type==='password',numeric=['integer','float','number'].includes(f.type)||selector.number!==undefined;fieldView=field(label,secret?'':(f.default??''),secret?'password':numeric?'number':'text');fieldView.input.required=f.required===true;read=()=>numeric?Number(fieldView.input.value):fieldView.input.value;if(secret)passwords.push(fieldView.input);if(selector.serial_port!==undefined||f.name==='port'&&setup.kind==='zigbee2mqtt')fieldView.input.placeholder=setup.kind==='zha'?'socket://coordinator-IP:6638':'tcp://coordinator-IP:6638'}
   else if(f.type==='constant'){readers.push(()=>[f.name,f.value??f.default]);continue}
   else{unsupported=true;target.append(element('p','caption','This connection needs a setup field that this VAutomate version cannot render: '+label));continue}
   fieldView.input.name=f.name;target.append(fieldView.wrap);if(setup.errors?.[f.name])window.VAutomateUI?.fieldError(fieldView.input,setup.errors[f.name].replaceAll('_',' '));readers.push(()=>[f.name,read()]);
 }}
 formFields(setup.fields,root,readers);const submit=button(setup.step==='z2m_install'?'Install Zigbee2MQTT':'Continue',async()=>{submit.disabled=true;try{const values=Object.fromEntries(readers.map(read=>read()));await send(values)}finally{for(const p of passwords)p.value=''}},'primary');submit.disabled=unsupported;root.append(submit,cancel());
}

function renderHomeCards(page){const view=dashboardLayout(),cards=view.cards||[];if(!cards.length)return;page.append(section(view.cards_title||'At a glance.'));const grid=element('div','dashboard-card-grid');for(const card of cards){let content;if(card.kind==='room'){const room=state.home.layout.rooms.find(r=>r.id===card.room_id);if(room)content=roomCard(room)}else{const entity=state.entities.get(card.entity_id);if(entity)content=deviceCard(entity)}if(!content)continue;if(card.title){const title=content.querySelector('h3');if(title)title.textContent=card.title}const wrapper=element('div','custom-dashboard-card');wrapper.dataset.span=String(card.span);wrapper.append(content);grid.append(wrapper)}page.append(grid)}
function manageDashboard(){
 const shared=admin(),view=dashboardLayout(),root=showDialog(shared?'Your dashboard.':'Your own view.',shared?'Arrange the shared dashboard your household starts with.':'Make this screen yours. Saved for your account on this device. Rooms, device assignments and system settings stay with your administrator.');root.append(button('Add a card',()=>dashboardCardEditor(null),'primary'));
 if(shared)root.append(button('Home details & Home buttons',openSetup),button('Rooms & device placement',manageRooms,'quiet'));else root.append(button('Use the shared dashboard',()=>{localStorage.removeItem(presentationKey());render();manageDashboard();toast('Shared dashboard restored for your view.')},'quiet'));
 const cards=view.cards||[];if(!cards.length)root.append(element('p','caption','Choose a light, fan, curtain, camera, reading or room shortcut.'));
 for(const [index,card] of cards.entries()){const row=element('section','panel dashboard-editor-row'),title=card.title||(card.kind==='room'?view.rooms.find(r=>r.id===card.room_id)?.name:entityName(state.entities.get(card.entity_id)))||'Dashboard card';row.append(element('h3','',title),element('p','caption',card.span===1?'Compact':card.span===2?'Wide':'Full width'));const actions=element('div','form-row');actions.append(button('Edit card',()=>dashboardCardEditor(card)),button('Move earlier',()=>moveDashboardCard(index,-1),'quiet'),button('Move later',()=>moveDashboardCard(index,1),'quiet'));actions.children[1].disabled=index===0;actions.children[2].disabled=index===cards.length-1;row.append(actions);root.append(row)}
 const title=field('Card section heading',view.cards_title||'At a glance.'),rooms=field('Show the rooms section on Home','','checkbox');rooms.input.checked=view.show_rooms!==false;root.append(title.wrap,rooms.wrap,button('Save dashboard options',async()=>{try{const layout=structuredClone(dashboardLayout());layout.cards_title=title.input.value;layout.show_rooms=rooms.input.checked;await saveDashboardView(layout);manageDashboard()}catch(error){dialogError(error)}},'primary'));
}
async function moveDashboardCard(index,delta){try{const layout=structuredClone(dashboardLayout()),cards=layout.cards,[item]=cards.splice(index,1);if(!item)return;cards.splice(index+delta,0,item);await saveDashboardView(layout);manageDashboard()}catch(error){dialogError(error)}}
async function dashboardCardEditor(original){
 const root=showDialog(original?'Edit dashboard card.':'Choose a card.','Pick something useful, then choose its size.'),epoch=state.dialogEpoch,card=original?structuredClone(original):{id:uid(),kind:'entity',span:1};let discovery;
 try{discovery=admin()?await client.request('discover'):{entities:[...state.entities.values()],registry:[]};if(epoch!==state.dialogEpoch)return}catch(error){dialogError(error);return}
 root.dataset.vaDraftKey='dashboard-card:'+(original?.id||'new');const type=selectField('Card type',[['entity','Everyday device or reading'],['room','Room shortcut']],card.kind),title=field('Card title (optional)',card.title||''),width=selectField('Card size',[[1,'Compact'],[2,'Wide'],[3,'Full width']],String(card.span)),pick=selectField('Content',[]);root.append(type.wrap,pick.wrap,title.wrap,width.wrap);
 const registry=new Map((discovery.registry||[]).map(e=>[e.entity_id,e]));let reveal=false;
 function choices(){const selected=pick.input.value||(type.input.value==='room'?card.room_id:card.entity_id)||'';pick.input.replaceChildren();const items=type.input.value==='room'?state.home.layout.rooms.map(r=>[r.id,r.name]):discovery.entities.filter(e=>reveal||StudioPresentation.everyday(e,registry.get(e.entity_id))||e.entity_id===card.entity_id||!admin()&&memberCardEligible(e)).map(e=>[e.entity_id,entityName(e)]);for(const [id,label] of [['','Choose content'],...items]){const option=element('option','',label);option.value=id;pick.input.append(option)}pick.input.value=selected};type.input.onchange=choices;choices();
 if(admin()){const system=field('Show system entities · administrator only','','checkbox');system.input.onchange=()=>{reveal=system.input.checked;choices()};root.append(system.wrap)}
 root.append(button('Save card',async()=>{try{if(!pick.input.value){window.VAutomateUI?.fieldError(pick.input,'Choose a device or room.');return}const value={id:card.id,kind:type.input.value,span:Number(width.input.value),...(title.input.value.trim()?{title:title.input.value.trim()}:{}),[type.input.value==='room'?'room_id':'entity_id']:pick.input.value},layout=structuredClone(dashboardLayout());layout.cards=original?(layout.cards||[]).map(c=>c.id===card.id?value:c):[...(layout.cards||[]),value];await saveDashboardView(layout);toast(admin()?'Dashboard card saved for your household.':'Your card is saved on this device.');manageDashboard()}catch(error){dialogError(error)}},'primary'));
 if(original)root.append(button('Remove card',async()=>{try{const layout=structuredClone(dashboardLayout());layout.cards=layout.cards.filter(c=>c.id!==card.id);await saveDashboardView(layout);manageDashboard()}catch(error){dialogError(error)}},'quiet'));root.append(button('Back to dashboard',manageDashboard,'quiet'));
}

function remoteExternal(url){if(window.__VA_NATIVE__?.call)return window.__VA_NATIVE__.call('app.tailscale.open',{url});window.open(url,'_blank','noopener,noreferrer');return Promise.resolve()}
async function openRemoteAccess(){
 if(!admin())return;
 const root=showDialog('Home, wherever you are.','Private remote access through your own Tailscale account. Your home sign-in and permissions still apply.'),epoch=state.dialogEpoch;
 const summary=element('p','remote-state','Checking your home…');summary.setAttribute('role','status');const steps=element('ol','remote-steps');for(const [title,copy] of [['Enable on your home','Install Tailscale and start it automatically with HAOS.'],['Sign in to Tailscale','Use the account that belongs to this customer’s home.'],['Connect your phone','Sign in to the same Tailscale network on your phone, then use the remote server address.']]){const row=element('li');row.append(element('strong','',title),element('p','caption',copy));steps.append(row)}
 const details=element('div','remote-readings'),attention=element('p','dialog-error');attention.setAttribute('role','alert');const address=field('Remote server address');address.input.readOnly=true;address.input.dataset.transient='';address.wrap.hidden=true;
 const actions=element('div','remote-actions');const enable=button('Enable remote access',remoteReview,'primary'),signin=button('Sign in to Tailscale',async()=>{signin.disabled=true;attention.textContent='';try{const result=await client.request('remote/signin');if(epoch!==state.dialogEpoch)return;if(result.url){login.href=result.url;login.hidden=false;login.focus()}else await refresh()}catch(error){attention.textContent=errorText(error)}finally{signin.disabled=false}},'primary');
 const login=element('a','primary remote-login','Continue to Tailscale sign-in');login.hidden=true;login.target='_blank';login.rel='noopener noreferrer';login.onclick=event=>{if(window.__VA_NATIVE__?.call){event.preventDefault();remoteExternal(login.href).catch(error=>attention.textContent=error.message)}};
 const save=button('Use this remote address in VAutomate',async()=>{try{await window.__VA_NATIVE__.call('app.remote.save',{url:address.input.value});toast('Remote server address saved for this home.')}catch(error){attention.textContent=error.message}},'primary');save.hidden=true;
 const phone=button('Get Tailscale for this device',()=>remoteExternal('https://tailscale.com/download').catch(error=>attention.textContent=error.message),'quiet'),check=button('Check connection',()=>refresh(),'quiet'),disable=button('Turn off remote access',()=>{const review=showDialog('Turn off remote access?','This stops Tailscale and disables start-on-boot. Its account is kept for reconnecting later. If you are away, this connection may end.');review.append(button('Turn off remote access',async()=>{try{await client.request('remote/disable',{confirmed:true});await openRemoteAccess()}catch(error){dialogError(error)}},'primary'),button('Keep remote access',openRemoteAccess,'quiet'))},'quiet');
 actions.append(enable,signin,login,save,phone,check,disable);root.append(summary,steps,details,address.wrap,attention,actions,element('p','caption','Automatic updates stay off. Tailscale must be connected on the device you use while away. Account approval or key renewal may occasionally be needed.'));
 let busy=false;
 async function refresh(){if(busy||epoch!==state.dialogEpoch)return;busy=true;try{const report=await client.request('remote/status');if(epoch!==state.dialogEpoch)return;const working=['installing','starting','stopping'].includes(report.phase);summary.textContent=working?({installing:'Installing Tailscale. This can take a few minutes.',starting:'Starting private remote access…',stopping:'Turning off remote access…'})[report.phase]:report.connected?'Connected · Your home is available on your Tailscale network.':report.vpn_state==='NeedsMachineAuth'?'Waiting for approval in your Tailscale account.':report.key_expired?'Sign in again to renew this home’s Tailscale access.':report.app_state==='started'?'Ready to sign in to Tailscale.':report.installed?'Tailscale is installed. Enable it to connect.':'Start with secure access to your home.';
 details.replaceChildren();for(const [label,value] of [['Home app',report.installed?'Installed':'Not installed'],['Start automatically',report.start_on_boot?'On':'Off'],['Process watchdog',report.watchdog?'On':'Off'],['Automatic updates',report.automatic_updates?'On':'Off']]){const row=element('div','settings-row');row.append(element('span','',label),element('strong','',value));details.append(row)}
 enable.hidden=report.app_state==='started'&&report.start_on_boot&&report.watchdog&&!report.configuration_attention&&!report.failure;enable.disabled=working||!report.supported||!!report.configuration_attention;signin.hidden=report.connected||report.app_state!=='started'||!!report.configuration_attention;signin.disabled=working;disable.hidden=!report.installed||report.app_state!=='started';disable.disabled=working;address.wrap.hidden=!report.remote_address;address.input.value=report.remote_address||'';save.hidden=!report.remote_address||!window.__VA_NATIVE__?.call;phone.hidden=false;
 attention.textContent=report.failure||(report.configuration_attention?'An existing Tailscale configuration uses advanced sharing. Your installer needs to review it; VAutomate has kept those settings.':report.status_attention?'Tailscale is running, but its connection is not verified yet. Check again shortly.':!report.supported?'Managed remote access requires a Home Assistant OS server.':'');
 if(report.connected){login.hidden=true;login.removeAttribute('href')}
 }catch(error){if(epoch===state.dialogEpoch){attention.textContent=errorText(error);summary.textContent='Connection status unavailable.'}}finally{busy=false}}
 await refresh();if(epoch===state.dialogEpoch)state.dialogTimer=setInterval(refresh,4000);
}
async function remoteReview(){if(!admin())return;showDialog('Preparing remote access.','Checking this home before making changes…');try{const plan=await client.request('remote/preview',{}),root=showDialog('Enable private remote access?','VAutomate will install the Home Assistant Community Tailscale app if needed, enable start-on-boot and watchdog, and keep automatic updates off. You will sign in directly with Tailscale.');const approve=field('I approve Tailscale setup for this home','','checkbox');root.append(approve.wrap,element('p','caption','This connects only this home server. It does not turn on public sharing, an exit node or access to the rest of your home network.'));const start=button('Install & enable',async()=>{start.disabled=true;try{await client.request('remote/enable',{approval_nonce:plan.approval_nonce,confirmed:approve.input.checked});await openRemoteAccess()}catch(error){dialogError(error);root.append(button('Check current setup',openRemoteAccess,'primary'))}},'primary');start.disabled=true;approve.input.onchange=()=>start.disabled=!approve.input.checked;root.append(start,button('Back',openRemoteAccess,'quiet'))}catch(error){dialogError(error)}}

/* VA_SHARED_UI_STATES_BEGIN */
/*
Copyright (c) 2014, Vladimir Agafonkin
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

*/
/*
 (c) 2011-2015, Vladimir Agafonkin
 SunCalc is a JavaScript library for calculating sun/moon position and light phases.
 https://github.com/mourner/suncalc
*/

(function () { 'use strict';

// shortcuts for easier to read formulas

var PI   = Math.PI,
    sin  = Math.sin,
    cos  = Math.cos,
    tan  = Math.tan,
    asin = Math.asin,
    atan = Math.atan2,
    acos = Math.acos,
    rad  = PI / 180;

// sun calculations are based on http://aa.quae.nl/en/reken/zonpositie.html formulas


// date/time constants and conversions

var dayMs = 1000 * 60 * 60 * 24,
    J1970 = 2440588,
    J2000 = 2451545;

function toJulian(date) { return date.valueOf() / dayMs - 0.5 + J1970; }
function fromJulian(j)  { return new Date((j + 0.5 - J1970) * dayMs); }
function toDays(date)   { return toJulian(date) - J2000; }


// general calculations for position

var e = rad * 23.4397; // obliquity of the Earth

function rightAscension(l, b) { return atan(sin(l) * cos(e) - tan(b) * sin(e), cos(l)); }
function declination(l, b)    { return asin(sin(b) * cos(e) + cos(b) * sin(e) * sin(l)); }

function azimuth(H, phi, dec)  { return atan(sin(H), cos(H) * sin(phi) - tan(dec) * cos(phi)); }
function altitude(H, phi, dec) { return asin(sin(phi) * sin(dec) + cos(phi) * cos(dec) * cos(H)); }

function siderealTime(d, lw) { return rad * (280.16 + 360.9856235 * d) - lw; }

function astroRefraction(h) {
    if (h < 0) // the following formula works for positive altitudes only.
        h = 0; // if h = -0.08901179 a div/0 would occur.

    // formula 16.4 of "Astronomical Algorithms" 2nd edition by Jean Meeus (Willmann-Bell, Richmond) 1998.
    // 1.02 / tan(h + 10.26 / (h + 5.10)) h in degrees, result in arc minutes -> converted to rad:
    return 0.0002967 / Math.tan(h + 0.00312536 / (h + 0.08901179));
}

// general sun calculations

function solarMeanAnomaly(d) { return rad * (357.5291 + 0.98560028 * d); }

function eclipticLongitude(M) {

    var C = rad * (1.9148 * sin(M) + 0.02 * sin(2 * M) + 0.0003 * sin(3 * M)), // equation of center
        P = rad * 102.9372; // perihelion of the Earth

    return M + C + P + PI;
}

function sunCoords(d) {

    var M = solarMeanAnomaly(d),
        L = eclipticLongitude(M);

    return {
        dec: declination(L, 0),
        ra: rightAscension(L, 0)
    };
}


var SunCalc = {};


// calculates sun position for a given date and latitude/longitude

SunCalc.getPosition = function (date, lat, lng) {

    var lw  = rad * -lng,
        phi = rad * lat,
        d   = toDays(date),

        c  = sunCoords(d),
        H  = siderealTime(d, lw) - c.ra;

    return {
        azimuth: azimuth(H, phi, c.dec),
        altitude: altitude(H, phi, c.dec)
    };
};


// sun times configuration (angle, morning name, evening name)

var times = SunCalc.times = [
    [-0.833, 'sunrise',       'sunset'      ],
    [  -0.3, 'sunriseEnd',    'sunsetStart' ],
    [    -6, 'dawn',          'dusk'        ],
    [   -12, 'nauticalDawn',  'nauticalDusk'],
    [   -18, 'nightEnd',      'night'       ],
    [     6, 'goldenHourEnd', 'goldenHour'  ]
];

// adds a custom time to the times config

SunCalc.addTime = function (angle, riseName, setName) {
    times.push([angle, riseName, setName]);
};


// calculations for sun times

var J0 = 0.0009;

function julianCycle(d, lw) { return Math.round(d - J0 - lw / (2 * PI)); }

function approxTransit(Ht, lw, n) { return J0 + (Ht + lw) / (2 * PI) + n; }
function solarTransitJ(ds, M, L)  { return J2000 + ds + 0.0053 * sin(M) - 0.0069 * sin(2 * L); }

function hourAngle(h, phi, d) { return acos((sin(h) - sin(phi) * sin(d)) / (cos(phi) * cos(d))); }
function observerAngle(height) { return -2.076 * Math.sqrt(height) / 60; }

// returns set time for the given sun altitude
function getSetJ(h, lw, phi, dec, n, M, L) {

    var w = hourAngle(h, phi, dec),
        a = approxTransit(w, lw, n);
    return solarTransitJ(a, M, L);
}


// calculates sun times for a given date, latitude/longitude, and, optionally,
// the observer height (in meters) relative to the horizon

SunCalc.getTimes = function (date, lat, lng, height) {

    height = height || 0;

    var lw = rad * -lng,
        phi = rad * lat,

        dh = observerAngle(height),

        d = toDays(date),
        n = julianCycle(d, lw),
        ds = approxTransit(0, lw, n),

        M = solarMeanAnomaly(ds),
        L = eclipticLongitude(M),
        dec = declination(L, 0),

        Jnoon = solarTransitJ(ds, M, L),

        i, len, time, h0, Jset, Jrise;


    var result = {
        solarNoon: fromJulian(Jnoon),
        nadir: fromJulian(Jnoon - 0.5)
    };

    for (i = 0, len = times.length; i < len; i += 1) {
        time = times[i];
        h0 = (time[0] + dh) * rad;

        Jset = getSetJ(h0, lw, phi, dec, n, M, L);
        Jrise = Jnoon - (Jset - Jnoon);

        result[time[1]] = fromJulian(Jrise);
        result[time[2]] = fromJulian(Jset);
    }

    return result;
};


// moon calculations, based on http://aa.quae.nl/en/reken/hemelpositie.html formulas

function moonCoords(d) { // geocentric ecliptic coordinates of the moon

    var L = rad * (218.316 + 13.176396 * d), // ecliptic longitude
        M = rad * (134.963 + 13.064993 * d), // mean anomaly
        F = rad * (93.272 + 13.229350 * d),  // mean distance

        l  = L + rad * 6.289 * sin(M), // longitude
        b  = rad * 5.128 * sin(F),     // latitude
        dt = 385001 - 20905 * cos(M);  // distance to the moon in km

    return {
        ra: rightAscension(l, b),
        dec: declination(l, b),
        dist: dt
    };
}

SunCalc.getMoonPosition = function (date, lat, lng) {

    var lw  = rad * -lng,
        phi = rad * lat,
        d   = toDays(date),

        c = moonCoords(d),
        H = siderealTime(d, lw) - c.ra,
        h = altitude(H, phi, c.dec),
        // formula 14.1 of "Astronomical Algorithms" 2nd edition by Jean Meeus (Willmann-Bell, Richmond) 1998.
        pa = atan(sin(H), tan(phi) * cos(c.dec) - sin(c.dec) * cos(H));

    h = h + astroRefraction(h); // altitude correction for refraction

    return {
        azimuth: azimuth(H, phi, c.dec),
        altitude: h,
        distance: c.dist,
        parallacticAngle: pa
    };
};


// calculations for illumination parameters of the moon,
// based on http://idlastro.gsfc.nasa.gov/ftp/pro/astro/mphase.pro formulas and
// Chapter 48 of "Astronomical Algorithms" 2nd edition by Jean Meeus (Willmann-Bell, Richmond) 1998.

SunCalc.getMoonIllumination = function (date) {

    var d = toDays(date || new Date()),
        s = sunCoords(d),
        m = moonCoords(d),

        sdist = 149598000, // distance from Earth to Sun in km

        phi = acos(sin(s.dec) * sin(m.dec) + cos(s.dec) * cos(m.dec) * cos(s.ra - m.ra)),
        inc = atan(sdist * sin(phi), m.dist - sdist * cos(phi)),
        angle = atan(cos(s.dec) * sin(s.ra - m.ra), sin(s.dec) * cos(m.dec) -
                cos(s.dec) * sin(m.dec) * cos(s.ra - m.ra));

    return {
        fraction: (1 + cos(inc)) / 2,
        phase: 0.5 + 0.5 * inc * (angle < 0 ? -1 : 1) / Math.PI,
        angle: angle
    };
};


function hoursLater(date, h) {
    return new Date(date.valueOf() + h * dayMs / 24);
}

// calculations for moon rise/set times are based on http://www.stargazing.net/kepler/moonrise.html article

SunCalc.getMoonTimes = function (date, lat, lng, inUTC) {
    var t = new Date(date);
    if (inUTC) t.setUTCHours(0, 0, 0, 0);
    else t.setHours(0, 0, 0, 0);

    var hc = 0.133 * rad,
        h0 = SunCalc.getMoonPosition(t, lat, lng).altitude - hc,
        h1, h2, rise, set, a, b, xe, ye, d, roots, x1, x2, dx;

    // go in 2-hour chunks, each time seeing if a 3-point quadratic curve crosses zero (which means rise or set)
    for (var i = 1; i <= 24; i += 2) {
        h1 = SunCalc.getMoonPosition(hoursLater(t, i), lat, lng).altitude - hc;
        h2 = SunCalc.getMoonPosition(hoursLater(t, i + 1), lat, lng).altitude - hc;

        a = (h0 + h2) / 2 - h1;
        b = (h2 - h0) / 2;
        xe = -b / (2 * a);
        ye = (a * xe + b) * xe + h1;
        d = b * b - 4 * a * h1;
        roots = 0;

        if (d >= 0) {
            dx = Math.sqrt(d) / (Math.abs(a) * 2);
            x1 = xe - dx;
            x2 = xe + dx;
            if (Math.abs(x1) <= 1) roots++;
            if (Math.abs(x2) <= 1) roots++;
            if (x1 < -1) x1 = x2;
        }

        if (roots === 1) {
            if (h0 < 0) rise = i + x1;
            else set = i + x1;

        } else if (roots === 2) {
            rise = i + (ye < 0 ? x2 : x1);
            set = i + (ye < 0 ? x1 : x2);
        }

        if (rise && set) break;

        h0 = h2;
    }

    var result = {};

    if (rise) result.rise = hoursLater(t, rise);
    if (set) result.set = hoursLater(t, set);

    if (!rise && !set) result[ye > 0 ? 'alwaysUp' : 'alwaysDown'] = true;

    return result;
};


// export as Node module / AMD module / browser variable
if (typeof exports === 'object' && typeof module !== 'undefined') module.exports = SunCalc;
else if (typeof define === 'function' && define.amd) define(SunCalc);
else window.SunCalc = SunCalc;

}());

/*
ISC License

Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

*/
/* Weather presentation. Lucide static 0.468.0 icons, ISC license in NOTICE. */
(()=>{'use strict';
const icons={"sun":[["circle",{"cx":"12","cy":"12","r":"4"}],["path",{"d":"M12 2v2"}],["path",{"d":"M12 20v2"}],["path",{"d":"m4.93 4.93 1.41 1.41"}],["path",{"d":"m17.66 17.66 1.41 1.41"}],["path",{"d":"M2 12h2"}],["path",{"d":"M20 12h2"}],["path",{"d":"m6.34 17.66-1.41 1.41"}],["path",{"d":"m19.07 4.93-1.41 1.41"}]],"moon":[["path",{"d":"M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"}]],"cloud":[["path",{"d":"M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"}]],"cloud-sun":[["path",{"d":"M12 2v2"}],["path",{"d":"m4.93 4.93 1.41 1.41"}],["path",{"d":"M20 12h2"}],["path",{"d":"m19.07 4.93-1.41 1.41"}],["path",{"d":"M15.947 12.65a4 4 0 0 0-5.925-4.128"}],["path",{"d":"M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6Z"}]],"cloud-moon":[["path",{"d":"M10.188 8.5A6 6 0 0 1 16 4a1 1 0 0 0 6 6 6 6 0 0 1-3 5.197"}],["path",{"d":"M13 16a3 3 0 1 1 0 6H7a5 5 0 1 1 4.9-6Z"}]],"cloud-rain":[["path",{"d":"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{"d":"M16 14v6"}],["path",{"d":"M8 14v6"}],["path",{"d":"M12 16v6"}]],"cloud-lightning":[["path",{"d":"M6 16.326A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 .5 8.973"}],["path",{"d":"m13 12-3 5h4l-3 5"}]],"cloud-snow":[["path",{"d":"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{"d":"M8 15h.01"}],["path",{"d":"M8 19h.01"}],["path",{"d":"M12 17h.01"}],["path",{"d":"M12 21h.01"}],["path",{"d":"M16 15h.01"}],["path",{"d":"M16 19h.01"}]],"cloud-hail":[["path",{"d":"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{"d":"M16 14v2"}],["path",{"d":"M8 14v2"}],["path",{"d":"M16 20h.01"}],["path",{"d":"M8 20h.01"}],["path",{"d":"M12 16v2"}],["path",{"d":"M12 22h.01"}]],"wind":[["path",{"d":"M12.8 19.6A2 2 0 1 0 14 16H2"}],["path",{"d":"M17.5 8a2.5 2.5 0 1 1 2 4H2"}],["path",{"d":"M9.8 4.4A2 2 0 1 1 11 8H2"}]],"cloud-fog":[["path",{"d":"M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"}],["path",{"d":"M16 17H7"}],["path",{"d":"M17 21H9"}]],"triangle-alert":[["path",{"d":"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{"d":"M12 9v4"}],["path",{"d":"M12 17h.01"}]],"cloud-off":[["path",{"d":"m2 2 20 20"}],["path",{"d":"M5.782 5.782A7 7 0 0 0 9 19h8.5a4.5 4.5 0 0 0 1.307-.193"}],["path",{"d":"M21.532 16.5A4.5 4.5 0 0 0 17.5 10h-1.79A7.008 7.008 0 0 0 10 5.07"}]]};
const conditions={sunny:['Sunny','sun'],'clear-night':['Clear night','moon'],cloudy:['Cloudy','cloud'],partlycloudy:['Partly cloudy','cloud-sun'],rainy:['Rainy','cloud-rain'],pouring:['Heavy rain','cloud-rain'],lightning:['Thunderstorms','cloud-lightning'],'lightning-rainy':['Thunderstorms and rain','cloud-lightning'],snowy:['Snow','cloud-snow'],'snowy-rainy':['Sleet','cloud-snow'],hail:['Hail','cloud-hail'],fog:['Fog','cloud-fog'],windy:['Windy','wind'],'windy-variant':['Windy and cloudy','wind'],exceptional:['Exceptional conditions','triangle-alert']};
let homeConfig=null;
function setHomeConfig(config){const latitude=Number(config?.latitude),longitude=Number(config?.longitude);homeConfig=config&&config.latitude!==null&&config.longitude!==null&&Number.isFinite(latitude)&&Number.isFinite(longitude)&&Math.abs(latitude)<=90&&Math.abs(longitude)<=180?{latitude,longitude}:null}
function daylight(attrs,sun,now){if(['above_horizon','below_horizon'].includes(sun?.state))return {night:sun.state==='below_horizon',source:'home-sun'};if(homeConfig&&window.SunCalc)try{const altitude=window.SunCalc.getPosition(now,homeConfig.latitude,homeConfig.longitude).altitude;if(Number.isFinite(altitude))return {night:altitude<-0.833*Math.PI/180,source:'home-location'}}catch{}if(typeof attrs.is_daytime==='boolean')return {night:!attrs.is_daytime,source:'weather-provider'};return {night:null,source:'unknown'}}
function present(entity,{sun,connected=true,now=new Date()}={}){const attrs=entity?.attributes||{},raw=String(entity?.state||'unknown').toLowerCase(),available=!!entity&&!['unknown','unavailable','none',''].includes(raw);const light=daylight(attrs,sun,now),night=light.night;const condition=raw==='sunny'&&night===true?'clear-night':raw;const mapped=conditions[condition],label=!entity?'Weather not configured':!available?'Weather unavailable':mapped?.[0]||'Condition not recognized';const numeric=v=>v!==null&&v!==undefined&&String(v).trim()!==''&&Number.isFinite(Number(v))?Number(v):null;return {raw,condition,label,icon:condition==='partlycloudy'&&night===true?'cloud-moon':mapped?.[1]||'cloud-off',night,daylightSource:light.source,available,connected,temperature:available?numeric(attrs.temperature):null,unit:attrs.temperature_unit||'°C',humidity:available?numeric(attrs.humidity):null,wind:available?numeric(attrs.wind_speed):null,windUnit:attrs.wind_speed_unit||'',updatedAt:entity?.last_updated||entity?.last_changed||null}}
function createIcon(condition){const key=typeof condition==='object'?condition.icon:conditions[condition]?.[1]||'cloud-off',svg=document.createElementNS('http://www.w3.org/2000/svg','svg');for(const [k,v] of Object.entries({viewBox:'0 0 24 24',width:'1em',height:'1em',fill:'none',stroke:'currentColor','stroke-width':'1.5','stroke-linecap':'round','stroke-linejoin':'round','aria-hidden':'true'}))svg.setAttribute(k,v);for(const [type,attrs] of icons[key]||icons['cloud-off']){const n=document.createElementNS(svg.namespaceURI,type);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);svg.append(n)}return svg}
window.VAutomateWeather={present,createIcon,setHomeConfig};
})();

/* VAutomate interaction states. Same implementation in Personal and Studio. */
(()=>{'use strict';
 if(window.VAutomateUI)return;
 let config={},region,lastSearch=null,model=null,rememberedScope='',captureTimer,decorateTimer,taskOwner=null;const pending=new Set(),editedForms=new WeakSet();
 const sensitive=/password|secret|token|credential|authorization|(?:^|_)(?:code|pin|psk|key)(?:$|_)/i;
 const privateName=value=>sensitive.test(String(value).replace(/([a-z0-9])([A-Z])/g,'$1_$2').replace(/[^a-z0-9]+/gi,'_'));
 const node=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
 function scope(){try{const value=config.scope?.();if(value)rememberedScope=value}catch{}return rememberedScope}
 function area(){return document.querySelector('dialog[open]')}
 function title(root){return root?.querySelector('[data-va-draft-key]')?.dataset.vaDraftKey||root?.dataset.vaDraftKey||root?.querySelector('h2,h1')?.textContent?.trim()||''}
 function modelEditor(root){return root?.dataset.vaModelEditor==='true'||root?.querySelector('[data-va-model-editor=true],.automation-editor')}
 function mountFeedback(){if(!region)return;const parent=area()||document.body;if(region.parentElement!==parent)parent.append(region)}
 function editor(root){return root&&!root.querySelector('input[type=password]')&&(root.dataset.vaEditor==='true'||modelEditor(root)||[...root.querySelectorAll('[aria-label]')].some(i=>['Room name','Home name','Automation name','Card title (optional)'].includes(i.getAttribute('aria-label'))))}
 function safe(value,depth=0){if(depth>24)return undefined;if(Array.isArray(value))return value.map(v=>safe(v,depth+1));if(value&&typeof value==='object'){const out={};for(const [k,v] of Object.entries(value)){if(!privateName(k)){const next=safe(v,depth+1);if(next!==undefined)out[k]=next}}return out}if(typeof value==='string'&&(/Bearer\s+|access_token=|password=/i.test(value)||value.length>64000))return undefined;return value}
 function key(type,id=''){return 'vautomate:ui-draft:v1:'+scope()+':'+type+':'+id}
 function store(type,id,value){if(!scope())return;try{sessionStorage.setItem(key(type,id),JSON.stringify({saved:Date.now(),value:safe(value)}))}catch{show('error','Draft could not be kept.','This browser blocked draft storage. Keep the editor open and save when connected.')}}
 function read(type,id){if(!scope())return null;try{const record=JSON.parse(sessionStorage.getItem(key(type,id))||'null');if(!record||Date.now()-record.saved>24*3600000)return null;return record.value}catch{return null}}
 function inputKey(input,counts){const name=input.getAttribute('aria-label')||input.name||input.id||input.closest('label')?.childNodes[0]?.textContent?.trim()||input.type;const count=counts[name]=(counts[name]||0)+1;return name+'::'+count}
 function allowed(input){return ['text','search','number','checkbox','radio','select-one','select-multiple','textarea','url','time','date'].includes(input.type)&&!input.matches('[data-actuator],[data-power-for],[role=switch]')&&!input.closest('.device,.entity-controls')&&!privateName([input.name,input.id,input.getAttribute('aria-label')].join(' '))}
 function captureModel(){if(model&&model.scope===scope())try{const value=model.get();if(JSON.stringify(safe(value))!==model.baseline)store('model',model.key,value)}catch{}}
 function captureDrafts(){
  captureModel();
  const root=area();if(!editor(root)||modelEditor(root))return;if(read('fields',title(root))&&!editedForms.has(root.querySelector('input,textarea,select')||root))return;const counts={},values=[];
  for(const input of root.querySelectorAll('input,textarea,select')){if(!allowed(input))continue;const id=inputKey(input,counts);values.push({id,value:input.value,checked:input.checked,type:input.type})}
  if(values.length<=250)store('fields',title(root),values);
 }
 function restoreFields(root){const saved=read('fields',title(root));if(!Array.isArray(saved))return;const counts={};for(const input of root.querySelectorAll('input,textarea,select')){if(!allowed(input))continue;const id=inputKey(input,counts),item=saved.find(v=>v.id===id);if(!item)continue;if(input.type==='checkbox'||input.type==='radio')input.checked=item.checked;else input.value=item.value;input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))}show('success','Draft restored.','Review your changes before saving.');root.querySelector('[data-va-restore]')?.remove()}
 function offerDraft(root){if(!editor(root)||modelEditor(root)||root.querySelector('[data-va-restore]')||root.querySelector('[data-va-model-draft]'))return;const saved=read('fields',title(root));if(!saved?.length)return;const b=node('button','va-draft-restore','Restore unsaved fields');b.type='button';b.dataset.vaRestore='';b.onclick=()=>restoreFields(root);root.append(b)}
 function show(type,heading,message,actionLabel,action){
  if(!region){region=node('section','va-feedback');region.id='va-ui-feedback';region.setAttribute('aria-live','polite');region.setAttribute('role','status');document.body.append(region)}
  taskOwner=null;mountFeedback();clearTimeout(show.timer);region.replaceChildren(node('strong','',heading),node('span','',message));region.dataset.state=type;region.hidden=false;
  if(actionLabel&&action){const b=node('button','',actionLabel);b.type='button';b.onclick=action;region.append(b)}
  const dismiss=node('button','va-feedback-close','\u00d7');dismiss.type='button';dismiss.setAttribute('aria-label','Dismiss status');dismiss.onclick=()=>region.hidden=true;region.append(dismiss);
  if(type==='success')show.timer=setTimeout(()=>region.hidden=true,6000);
 }
 function fieldError(input,message){if(!input||input.type==='hidden')return;let error=input.dataset.vaError?document.getElementById(input.dataset.vaError):null;if(!error){error=node('small','va-field-error');error.dataset.vaFieldError='';error.id='va-error-'+Math.random().toString(36).slice(2);input.dataset.vaError=error.id;error.setAttribute('role','alert');input.insertAdjacentElement('afterend',error)}error.textContent=message;input.setAttribute('aria-invalid','true');input.setAttribute('aria-describedby',[...new Set([...(input.getAttribute('aria-describedby')||'').split(/\s+/).filter(Boolean),error.id])].join(' '))}
 function validate(root=area()){if(!root)return true;let first;for(const input of root.querySelectorAll('input,select,textarea')){if(input.disabled||input.closest('[hidden]')||input.type==='hidden')continue;if(!input.checkValidity()){fieldError(input,input.validationMessage);first??=input}}if(first){first.focus();return false}return true}
 function failure(error,options={}){const code=String(error?.code||''),message=String(error?.message||error||'Your home could not complete this request.').replace(/Bearer\s+[^\s]+/gi,'Bearer [redacted]').replace(/((?:password|token|secret|credential)[\"']?\s*[:=]\s*[\"']?)[^\"'\s,}]+/gi,'$1[redacted]');if(/not_allowed|unauthor|forbidden|permission/i.test(code+' '+message)){show('permission','This action needs permission.',message+' Ask the home administrator if your access needs changing.');return}if(/invalid_auth|auth_invalid|expired.*session|sign.in.*not.accepted/i.test(code+' '+message)){sessionExpired();return}const root=area();if(/invalid_input|validation|username_taken|invalid_password|confirmation_required/.test(code)&&root){const invalid=[...root.querySelectorAll('input,select,textarea')].find(i=>!i.checkValidity());if(invalid)fieldError(invalid,message);else if(code==='invalid_password')fieldError(root.querySelector('input[type=password]'),message);else if(code==='confirmation_required')fieldError([...root.querySelectorAll('input[type=checkbox]')].find(i=>!i.checked&&/approve|confirm|ready|acknowledge/i.test(i.getAttribute('aria-label')||'')),message)}show('error','Your home needs a check.',message,options.readOnly?'Try again':'Check current status',options.readOnly&&options.retry?options.retry:()=>config.refresh?.())}
 function sessionExpired(){captureDrafts();show('session','Please sign in again.','Safe drafts are kept in this browser session when storage is available. Passwords and security codes are never saved.','Sign in',()=>config.signin?.())}
 function connection(connected,message){document.body.dataset.vaConnection=connected?'online':'offline';if(connected){if(region&&['offline','session'].includes(region.dataset.state))region.hidden=true;return}if(config.hasSession?.())show('offline',navigator.onLine?'Your home is reconnecting.':'This device is offline.',message||'Your last view is kept. Live controls will return when connected.','Check connection',()=>config.refresh?.())}
 function taskNotice(marker){if(region&&!region.hidden&&['error','permission','session','offline','success'].includes(region.dataset.state))return;show(marker.phase,marker.phase==='slow'?'Your home is taking longer.':marker.options.label||'Working with your home.',marker.phase==='slow'?'Please wait for its response. An action will never be resubmitted automatically.':'Your view is kept while the home responds.');taskOwner=marker}
 function task(operation,promise,options={}){
  const marker={options,phase:null};pending.add(marker);
  const t=setTimeout(()=>{marker.phase='loading';taskNotice([...pending].find(m=>m.phase)||marker)},1500),slow=setTimeout(()=>{marker.phase='slow';taskNotice([...pending].find(m=>m.phase)||marker)},8000);
  return Promise.resolve(promise).catch(error=>{failure(error,options);throw error}).finally(()=>{clearTimeout(t);clearTimeout(slow);pending.delete(marker);if(taskOwner===marker){region.hidden=true;taskOwner=null;const next=[...pending].find(m=>m.phase);if(next)taskNotice(next)}})
 }
 function decorate(){mountFeedback();const root=area();offerDraft(root);for(const empty of document.querySelectorAll('.empty,.empty-state,#picklist,.entity-library,.management-list')){const existing=empty.querySelector('.va-empty-action');if(existing){const label=lastSearch?.isConnected&&lastSearch.value?'Clear search':'Choose a connection';if(existing.textContent!==label)existing.textContent=label;}if(!/^No (?:matching|connected|selected)|^A little quiet|^Your home starts/i.test(empty.textContent.trim())||empty.querySelector('button'))continue;const b=node('button','va-empty-action',lastSearch?.isConnected&&lastSearch.value?'Clear search':'Choose a connection');b.type='button';b.onclick=()=>{if(lastSearch?.isConnected&&lastSearch.value){lastSearch.value='';lastSearch.dispatchEvent(new Event('input',{bubbles:true}));lastSearch.focus()}else config.setup?.()};empty.append(b)}}
 function init(settings){config=settings;document.addEventListener('focusin',event=>{const i=event.target;if(i.matches('input,textarea,select')&&/search|find/i.test(i.getAttribute('aria-label')||i.placeholder||i.type)){lastSearch=i;clearTimeout(decorateTimer);decorateTimer=setTimeout(decorate,100)}});document.addEventListener('input',event=>{const input=event.target,root=area();if(root?.contains(input))editedForms.add(root.querySelector('input,textarea,select')||root);if(/search|find/i.test(input.getAttribute?.('aria-label')||input.placeholder||input.type)){lastSearch=input;clearTimeout(decorateTimer);decorateTimer=setTimeout(decorate,100)}if(input.getAttribute?.('aria-invalid')==='true'&&input.checkValidity()){input.removeAttribute('aria-invalid');document.getElementById(input.dataset.vaError)?.remove();const ids=(input.getAttribute('aria-describedby')||'').split(/\s+/).filter(id=>id&&id!==input.dataset.vaError);if(ids.length)input.setAttribute('aria-describedby',ids.join(' '));else input.removeAttribute('aria-describedby');delete input.dataset.vaError}clearTimeout(captureTimer);captureTimer=setTimeout(captureDrafts,300)});document.addEventListener('change',event=>{const root=area();if(root?.contains(event.target))editedForms.add(root.querySelector('input,textarea,select')||root);clearTimeout(captureTimer);captureTimer=setTimeout(captureDrafts,300)});document.addEventListener('invalid',event=>fieldError(event.target,event.target.validationMessage),true);document.addEventListener('click',event=>{const button=event.target.closest('button');if(!button)return;if(!/^Restore /i.test(button.textContent.trim()))captureDrafts();if((navigator.onLine===false||config.connected?.()===false)&&button.matches('[role=switch],[data-actuator],[data-room-master],[data-power-for]')){event.preventDefault();event.stopImmediatePropagation();connection(false);return}if(/^(Save|Create|Review|Continue|Begin|Install|Publish)/i.test(button.textContent.trim())&&button.closest('dialog')&&!validate(button.closest('dialog'))){event.preventDefault();event.stopImmediatePropagation()}},true);window.addEventListener('offline',()=>connection(false));window.addEventListener('online',()=>{if(config.hasSession?.())config.refresh?.()});document.addEventListener('cancel',captureDrafts,true);document.addEventListener('close',mountFeedback,true);window.addEventListener('pagehide',captureDrafts);document.addEventListener('visibilitychange',()=>{if(document.hidden)captureDrafts()});new MutationObserver(()=>{clearTimeout(decorateTimer);decorateTimer=setTimeout(decorate,100)}).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['open']});decorate()}
 window.VAutomateUI={init,show,failure,connection,task,validate,fieldError,captureDrafts,sessionExpired,readModel:(type,id)=>read('model',type+':'+id),trackModel:(type,id,get)=>{captureModel();model={key:type+':'+id,scope:scope(),get,baseline:JSON.stringify(safe(get()))}},clearFields:()=>{const root=area();if(root)try{sessionStorage.removeItem(key('fields',title(root)))}catch{}},clearModel:(type,id)=>{try{sessionStorage.removeItem(key('model',type+':'+id))}catch{}if(model?.key===type+':'+id)model=null},safe};
})();


(()=>{const ui=window.VAutomateUI;
ui.init({scope:()=>state.home?.user?.id?'studio:'+location.origin+':'+(window.__VA_HOME_PROFILE__||'')+':'+state.home.user.id:'',connected:()=>client.connected,hasSession:()=>!!(state.home||client.access||client.refreshToken),signin:connection,setup:()=>admin()?navigate('manage'):connection(),refresh:()=>{if(client.connected)refreshSnapshot();else if(client.access)client.open();else connection()}});
const request=client.request.bind(client);client.request=(operation,payload={})=>ui.task(operation,request(operation,payload),{readOnly:/^(bootstrap|snapshot|discover|history|care|activity|camera\/snapshot|.*\/(?:status|list|library|me|traces))$/.test(operation),retry:()=>client.request(operation,payload)});
const status=client.onstatus;client.onstatus=(message,connected)=>{status(message,connected);ui.connection(connected,message)};
const login=client.onlogin;client.onlogin=()=>{ui.captureDrafts();login()};
const error=dialogError;dialogError=function(value){error(value);if(['invalid_password','invalid_auth'].includes(value.code))ui.fieldError(document.querySelector('#dialog input[type=password]'),errorText(value))};
})();

/* VA_SHARED_UI_STATES_END */
