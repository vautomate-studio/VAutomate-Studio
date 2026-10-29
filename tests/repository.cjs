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
const manifestFile=path.join(root,'custom_components/vautomate_studio/manifest.json'),manifestOriginal=fs.readFileSync(manifestFile),payloadFile=path.join(root,'installer/vautomate_installer/payload.json'),payloadOriginal=JSON.parse(fs.readFileSync(payloadFile));
function build(){return cp.spawnSync(process.env.VAM_TEST_PYTHON||'python',[path.join(root,'tools/build_installer.py')],{cwd:root,encoding:'utf8'})}
let packageHash;
try{fs.writeFileSync(manifestFile,manifestOriginal.toString('utf8').replace(/\r?\n/g,'\r\n'));assert.equal(verify().status,1,'A changed runtime checksum must fail');const rebuilt=build();assert.equal(rebuilt.status,0,rebuilt.stdout+rebuilt.stderr);packageHash=JSON.parse(rebuilt.stdout.trim()).sha256;assert.deepEqual(fs.readFileSync(manifestFile),manifestOriginal,'Builder must restore canonical LF bytes');assert.deepEqual(JSON.parse(fs.readFileSync(payloadFile)).files,payloadOriginal.files,'Windows and Git/Linux source hashes must match')}finally{fs.writeFileSync(manifestFile,manifestOriginal);const repeated=build();assert.equal(repeated.status,0);if(packageHash)assert.equal(JSON.parse(repeated.stdout.trim()).sha256,packageHash,'Repeated source kits must be byte-for-byte identical')}
assert.equal(verify().status,0);console.log('PASS: clean source, private-value redaction, stale assets, corrupted characters, portable hashes and reproducible source kit.');
