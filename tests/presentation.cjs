/* Pure view isolation checks. No browser, transport or household operations. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('frontend/app.js','utf8').split('/* STUDIO_PRESENTATION_BEGIN */')[1].split('/* STUDIO_PRESENTATION_END */')[0];
const context={structuredClone};vm.createContext(context);vm.runInContext(source+';this.presentation=StudioPresentation',context);const p=context.presentation;
const entity=(entity_id,attributes={})=>({entity_id,attributes});
assert(p.everyday(entity('light.ceiling')));assert(p.everyday(entity('fan.ceiling')));assert(p.everyday(entity('sensor.temperature',{device_class:'temperature'})));assert(!p.everyday(entity('sensor.integration_health')));assert(!p.everyday(entity('sensor.device_temperature',{device_class:'temperature'}),{diagnostic:true}));assert(!p.everyday(entity('switch.led'),{disabled:true}));assert(!p.everyday(entity('input_boolean.internal_pause')));
const base={name:'Shared home',rooms:[{id:'living',name:'Living',entities:['light.ceiling']}],cards:[{id:'room-card',kind:'room',room_id:'living',span:1},{id:'light-card',kind:'entity',entity_id:'light.ceiling',span:1}],quick_actions:[]};
const removed=p.removeRoom(base,'living');assert.equal(removed.rooms.length,0);assert.equal(removed.cards.length,1);assert.equal(removed.cards[0].entity_id,'light.ceiling');assert.equal(base.rooms.length,1);assert.equal(base.cards.length,2);
const view=p.personal(base,{schema:1,name:'Injected',rooms:[],quick_actions:[{entity_id:'switch.system'}],show_rooms:false,cards:[{id:'one',kind:'entity',entity_id:'light.ceiling',span:2},{id:'bad',kind:'entity',entity_id:'switch.system',span:1},{id:'missing',kind:'room',room_id:'deleted',span:1},{id:'one',kind:'room',room_id:'living',span:1},{id:'badspan',kind:'room',room_id:'living',span:100}]},new Set(['light.ceiling']));
assert.equal(view.name,'Shared home');assert.equal(view.rooms,base.rooms);assert.equal(view.quick_actions,base.quick_actions);assert.equal(view.cards.length,1);assert.equal(view.cards[0].span,2);assert.equal(view.show_rooms,false);assert.equal(base.cards[0].span,1);
assert.equal(p.personal(base,{schema:999,cards:[]},new Set()),base);
console.log('PASS: everyday device filtering, room-shortcut cleanup, member view isolation and stale/forged card rejection.');
