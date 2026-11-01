const vm=require('vm'),fs=require('fs'),assert=require('assert/strict'),context={window:{}};vm.createContext(context);vm.runInContext(fs.readFileSync('shared/suncalc.js','utf8'),context);vm.runInContext(fs.readFileSync('shared/weather.js','utf8'),context);const present=context.window.VAutomateWeather.present;
assert.equal(present({state:'sunny',attributes:{}},{sun:{state:'below_horizon'}}).label,'Clear night');assert.equal(present({state:'sunny',attributes:{}},{sun:{state:'above_horizon'}}).label,'Sunny');assert.equal(present({state:'rainy',attributes:{}},{sun:{state:'below_horizon'}}).label,'Rainy');assert.equal(present({state:'partlycloudy',attributes:{}},{sun:{state:'below_horizon'}}).icon,'cloud-moon');assert.equal(present(null).label,'Weather not configured');assert.equal(present({state:'unavailable',attributes:{temperature:33}}).temperature,null);assert.equal(present({state:'unknown'}).label,'Weather unavailable');assert.equal(present({state:'sunny',attributes:{is_daytime:false,temperature:'27.2'}}).temperature,27.2);console.log('PASS: condition-specific weather, authoritative night state and no invented sunny fallback.');

const weather=context.window.VAutomateWeather;weather.setHomeConfig({latitude:51.5,longitude:0});
const staleDay={state:'sunny',attributes:{is_daytime:true}};
assert.equal(weather.present(staleDay,{now:new Date('2026-11-01T00:00:00Z')}).label,'Clear night');
assert.equal(weather.present(staleDay,{now:new Date('2026-11-01T00:00:00Z')}).daylightSource,'home-location');
assert.equal(weather.present({state:'sunny',attributes:{is_daytime:false}},{now:new Date('2026-11-01T12:00:00Z')}).label,'Sunny');
assert.equal(weather.present(staleDay,{sun:{state:'below_horizon'},now:new Date('2026-11-01T12:00:00Z')}).label,'Clear night');
assert(!JSON.stringify(weather.present(staleDay)).includes('latitude'));weather.setHomeConfig(null);
console.log('PASS: server-location night fallback, stale-provider override and no coordinate exposure.');
