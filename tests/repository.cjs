/* Check that publication verification actually blocks unsafe/stale source. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..'),script=path.join(root,'tools/verify_repository.py');
function verify(){const result=cp.spawnSync(process.env.VAM_TEST_PYTHON||'python',[script],{cwd:root,encoding:'utf8'});if(result.error)throw result.error;return result}
const baseline=verify();assert.equal(baseline.status,0,baseline.stdout+baseline.stderr);
const file=path.join(root,'.env.repository-check');assert(!fs.existsSync(file),'A pre-existing private check file must be reviewed first');
const synthetic='gh'+'p_'+'a'.repeat(36);
try{fs.writeFileSync(file,synthetic);const result=verify();assert.equal(result.status,1);assert(result.stdout.includes('private or generated file'));assert(!result.stdout.includes(synthetic),'Private values must not appear in reports')}finally{fs.unlinkSync(file)}
const client=path.join(root,'android/app/src/main/assets/vautomate-customer/client.js'),original=fs.readFileSync(client);
try{fs.appendFileSync(client,'\n/* synthetic stale asset */\n');const result=verify();assert.equal(result.status,1);assert(result.stdout.includes('stale frontend copy'))}finally{fs.writeFileSync(client,original)}
const app=path.join(root,'frontend/app.js'),appOriginal=fs.readFileSync(app);
try{fs.appendFileSync(app,'\n/* '+String.fromCharCode(0xc2,0xb7)+' */\n');const result=verify();assert.equal(result.status,1);assert(result.stdout.includes('corrupted display characters'))}finally{fs.writeFileSync(app,appOriginal)}
assert.equal(verify().status,0);console.log('PASS: clean repository, private-file rejection with redacted output, stale-asset and corrupted-character detection.');
