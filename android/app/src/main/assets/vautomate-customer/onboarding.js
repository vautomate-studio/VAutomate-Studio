/* First-owner setup on a preinstalled VAutomate gateway. No tokens or passwords are stored here. */
(()=>{'use strict';
 const paths=new Set(['/api/vautomate_studio/v1/health','/api/onboarding','/api/onboarding/users','/api/onboarding/core_config','/api/onboarding/analytics','/api/onboarding/integration','/api/config/config_entries/flow']);
 async function request(client,path,data){
  if(!paths.has(path)&&!/^\/api\/config\/config_entries\/flow\/(?:[a-f0-9]{32}|[0-9A-HJKMNP-TV-Z]{26})$/.test(path))throw new StudioError('invalid_path','Unsupported home setup request.');
  const publicRoute=path==='/api/onboarding'||path==='/api/onboarding/users';
  if(!publicRoute&&!client.access)throw new StudioError('invalid_auth','Sign in to finish setting up your home.');
  let response;try{response=await fetch(location.origin+path,{method:data===undefined?'GET':'POST',headers:{...(data===undefined?{}:{'Content-Type':'application/json'}),...(!publicRoute?{Authorization:'Bearer '+client.access}:{})},...(data===undefined?{}:{body:JSON.stringify(data)}),credentials:'same-origin',redirect:'error',signal:AbortSignal.timeout(20000)})}catch{throw new StudioError('setup_unavailable','Your home did not respond. Check the connection before trying again.')}
  if(path==='/api/onboarding'&&[401,404].includes(response.status))return null;
  if(path==='/api/vautomate_studio/v1/health'&&[404,503].includes(response.status))return null;
  if(!response.ok)throw new StudioError(response.status===403?'not_allowed':'setup_unavailable',response.status===403?'Only a home administrator can finish setup.':'Your home could not confirm this setup step. Existing account details have been kept.');
  try{return await response.json()}catch{throw new StudioError('setup_unavailable','Your home returned an unsupported setup response.')}
 }
 async function probe(client){const steps=await request(client,'/api/onboarding');if(steps===null)return null;if(!Array.isArray(steps)||steps.some(step=>typeof step?.step!=='string'||typeof step.done!=='boolean'))throw new StudioError('incompatible','This server needs a compatible VAutomate setup update.');return {needsOwner:steps.some(step=>step.step==='user'&&!step.done),steps}}
 async function complete(client){
  const state=await probe(client);
  if(state?.needsOwner)throw new StudioError('invalid_auth','Create your home owner first.');
  if(state){const allowed=new Set(['user','core_config','analytics','integration']);if(state.steps.some(step=>!step.done&&!allowed.has(step.step)))throw new StudioError('incompatible','An additional server setup step needs installer attention.');
   for(const step of ['core_config','analytics','integration'])if(state.steps.some(value=>value.step===step&&!value.done))await request(client,'/api/onboarding/'+step,step==='integration'?{client_id:client.clientId,redirect_uri:location.origin+location.pathname}:{});
  }
  let flow=await request(client,'/api/config/config_entries/flow',{handler:'vautomate_studio',show_advanced_options:false});
  if(flow.type==='form'&&flow.step_id==='user'&&Array.isArray(flow.data_schema)&&flow.data_schema.length===0&&/^(?:[a-f0-9]{32}|[0-9A-HJKMNP-TV-Z]{26})$/.test(flow.flow_id))flow=await request(client,'/api/config/config_entries/flow/'+flow.flow_id,{});
  if(flow.type!=='create_entry'&&!(flow.type==='abort'&&flow.reason==='already_configured'))throw new StudioError('installer_required','The VAutomate server package needs installer attention. Your owner account was kept.');
  let initialized=false;for(let attempt=0;attempt<30;attempt++){const health=await request(client,'/api/vautomate_studio/v1/health');if(health){if(health.api_version!==1)throw new StudioError('incompatible','Your home needs a compatible VAutomate service.');if(health.initialized===true){initialized=true;break}}await new Promise(resolve=>setTimeout(resolve,1000))}if(!initialized)throw new StudioError('setup_pending','Your home is still finishing setup. Continue shortly; your owner account was kept.');
  client.open();
 }
 async function create(client,values){
  const name=String(values.name||'').trim(),username=String(values.username||'').trim().toLowerCase(),password=values.password;
  if(!name||name.length>80||! /^[a-z0-9][a-z0-9_.-]{2,47}$/.test(username)||typeof password!=='string'||password.length<12||password.length>256)throw new StudioError('invalid_input','Use a name, a username with 3–48 letters/numbers, and a password with at least 12 characters.');
  const before=await probe(client);if(!before?.needsOwner)throw new StudioError('already_configured','This home already has an owner. Sign in with the existing account.');
  const result=await request(client,'/api/onboarding/users',{client_id:client.clientId,name,username,password,language:'en'});
  if(typeof result.auth_code!=='string'||!result.auth_code)throw new StudioError('setup_unavailable','The owner account was created, but sign-in needs another attempt.');
  const session=await client.auth('/auth/token',{grant_type:'authorization_code',code:result.auth_code,client_id:client.clientId},true);
  client.closed=false;client.applySession(session);await client.remember();
  await complete(client);
 }
 function render(client,root,onError){
  root.replaceChildren();const form=document.createElement('form');form.className='owner-setup';const fields={};
  for(const [key,label,type,autocomplete]of [['name','Your name','text','name'],['username','Choose a username','text','username'],['password','Choose a password','password','new-password'],['confirmation','Repeat your password','password','new-password']]){const wrapper=document.createElement('label');wrapper.className='field';wrapper.append(document.createTextNode(label));const input=document.createElement('input');input.type=type;input.autocomplete=autocomplete;input.required=true;input.setAttribute('aria-label',label);input.maxLength=key==='name'?80:key==='username'?48:256;if(type==='password')input.minLength=12;wrapper.append(input);form.append(wrapper);fields[key]=input}
  const hint=document.createElement('p');hint.className='caption';hint.textContent='Use at least 12 characters. Your password stays on this home server. The owner controls household access.';form.append(hint);
  const consent=document.createElement('label');consent.className='select-device';const acknowledge=document.createElement('input');acknowledge.type='checkbox';acknowledge.required=true;acknowledge.setAttribute('aria-label','I am setting up a new home on this server');consent.append(acknowledge,document.createTextNode('I am setting up a new home on this server'));form.append(consent);
  const submit=document.createElement('button');submit.type='submit';submit.className='primary';submit.textContent='Create owner & set up home';form.append(submit);
  let busy=false;form.onsubmit=async event=>{event.preventDefault();if(busy)return;if(fields.password.value!==fields.confirmation.value){onError(new StudioError('invalid_input','The two passwords need to match.'));return}busy=true;submit.disabled=true;try{await create(client,{name:fields.name.value,username:fields.username.value,password:fields.password.value})}catch(error){onError(error);if(client.access){for(const input of Object.values(fields))input.disabled=true;submit.textContent='Continue home setup';form.onsubmit=async e=>{e.preventDefault();if(busy)return;busy=true;submit.disabled=true;try{await complete(client)}catch(next){onError(next)}finally{busy=false;submit.disabled=false}}}}finally{fields.password.value='';fields.confirmation.value='';busy=false;submit.disabled=false}};
  root.append(form);
 }
 window.StudioOnboarding={probe,create,complete,render};
})();
