/* Coordinator address rendering only; never contacts a device. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('frontend/app.js','utf8').split('/* COORDINATOR_ADDRESS_BEGIN */')[1].split('/* COORDINATOR_ADDRESS_END */')[0];
const context={URL};vm.createContext(context);vm.runInContext(src+';this.address=coordinatorAddress',context);const address=context.address;
assert.equal(address('coordinator.local','6638','zha'),'socket://coordinator.local:6638');
assert.equal(address('coordinator.local',6638,'zigbee2mqtt'),'tcp://coordinator.local:6638');
assert.equal(address('fd00::1',6638,'zha'),'socket://[fd00::1]:6638');
for(const [host,port] of [['',6638],['name/path',6638],['name@other',6638],['name?secret',6638],['name',0],['name',70000],['name',80],['name',NaN]])assert.throws(()=>address(host,port,'zha'));
console.log('PASS: USB/network coordinator address generation and invalid-field rejection without device traffic.');
