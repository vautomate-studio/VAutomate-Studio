"""Inert auth-adapter tests. Real disposable account verification is separate."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

class InvalidUser(Exception):pass
class InvalidAuth(Exception):pass

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/ha_household.py'
spec=importlib.util.spec_from_file_location('studio_product.ha_household',path);module=importlib.util.module_from_spec(spec)
provider_module=SimpleNamespace(async_get_provider=lambda hass:hass.provider,InvalidUser=InvalidUser,InvalidAuth=InvalidAuth)
with patch.dict(sys.modules,{'homeassistant.auth.const':SimpleNamespace(GROUP_ID_ADMIN='system-admin',GROUP_ID_USER='system-users',GROUP_ID_READ_ONLY='system-read-only'),'homeassistant.auth.providers':SimpleNamespace(homeassistant=provider_module)}):spec.loader.exec_module(module)

def user(identity='person',role='system-users',owner=False):return SimpleNamespace(id=identity,name='A person',is_owner=owner,is_admin=role=='system-admin',is_active=True,system_generated=False,groups=[SimpleNamespace(id=role)],local_only=False,credentials=[SimpleNamespace(auth_provider_type='homeassistant',data={'username':identity,'password_hash':'NEVER_EXPORT'})],refresh_tokens={'one':'TOKEN_ONE','two':'TOKEN_TWO'})

class Provider:
    def __init__(self):self.accounts={'existing':'PRIVATE'};self.removed=[];self.changed=[]
    async def async_add_auth(self,username,password):
        if username in self.accounts:raise InvalidUser()
        self.accounts[username]=password
    async def async_remove_auth(self,username):
        self.removed.append(username)
        if username not in self.accounts:raise InvalidUser()
        del self.accounts[username]
    async def async_get_or_create_credentials(self,data):return SimpleNamespace(data=data,auth_provider_type='homeassistant')
    async def async_validate_login(self,username,password):
        if password!='fixture-password':raise InvalidAuth()
    async def async_change_password(self,username,password):self.changed.append(username)

class Auth:
    def __init__(self):self.people={'person':user(),'owner':user('owner','system-admin',True)};self.removed=[];self.revoked=[];self.fail_link=False
    async def async_get_user(self,identity):return self.people.get(identity)
    async def async_get_users(self):return list(self.people.values())
    async def async_create_user(self,name,**options):
        created=user('new',options['group_ids'][0]);created.name=name;created.local_only=options['local_only'];created.credentials=[];self.people['new']=created;return created
    async def async_link_user(self,person,credentials):
        if self.fail_link:raise RuntimeError('PRIVATE auth failure')
        person.credentials.append(credentials)
    async def async_remove_user(self,person):self.removed.append(person.id);del self.people[person.id]
    async def async_update_user(self,person,**options):person.updated=options
    def async_remove_refresh_token(self,token):self.revoked.append(token)

class HAAccountTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.auth=Auth();self.provider=Provider();self.delayed=[];self.hass=SimpleNamespace(auth=self.auth,provider=self.provider,loop=SimpleNamespace(call_later=lambda delay,fn,*args:self.delayed.append((fn,args))))
        self.adapter=module.HAHousehold(self.hass)
    async def test_public_accounts_never_export_hashes_tokens_or_system_accounts(self):
        system=user('system');system.system_generated=True;self.auth.people['system']=system;report=await self.adapter.users();self.assertEqual(len(report),2);self.assertNotIn('NEVER_EXPORT',str(report));self.assertNotIn('TOKEN_',str(report))
    async def test_viewer_and_member_groups_map_to_distinct_roles(self):
        self.auth.people['person'].groups=[SimpleNamespace(id='system-read-only')];self.assertEqual((await self.adapter.user('person'))['role'],'viewer')
        self.auth.people['person'].groups=[SimpleNamespace(id='custom')];self.assertEqual((await self.adapter.user('person'))['role'],'custom')
    async def test_new_account_has_only_the_reviewed_role(self):
        result=await self.adapter.create({'username':'family','name':'Family','role':'viewer','local_only':True},'PRIVATE');self.assertEqual(result['role'],'viewer');self.assertTrue(result['local_only']);self.assertEqual(result['username'],'family')
    async def test_duplicate_username_never_removes_an_existing_account_or_credentials(self):
        with self.assertRaises(Exception):await self.adapter.create({'username':'existing','name':'Family','role':'member','local_only':False},'PRIVATE')
        self.assertEqual(self.auth.removed,[]);self.assertEqual(self.provider.removed,[]);self.assertEqual(self.provider.accounts['existing'],'PRIVATE')
    async def test_partial_create_rolls_back_only_its_new_resources(self):
        self.auth.fail_link=True
        with self.assertRaises(RuntimeError):await self.adapter.create({'username':'family','name':'Family','role':'member','local_only':False},'PRIVATE')
        self.assertEqual(self.auth.removed,['new']);self.assertEqual(self.provider.removed,['family']);self.assertIn('existing',self.provider.accounts);self.assertNotIn('family',self.provider.accounts)
    async def test_owner_and_system_account_mutations_rejected_again_at_adapter(self):
        for call in [self.adapter.remove('owner'),self.adapter.update('owner',{})]:
            with self.assertRaises(Exception):await call
        self.assertEqual(self.auth.removed,[])
    async def test_access_updates_revoke_existing_sessions(self):
        await self.adapter.update('person',{'name':'Family','role':'viewer','active':False,'local_only':True});self.assertEqual(self.auth.people['person'].updated['group_ids'],['system-read-only']);self.assertEqual(self.auth.revoked,['TOKEN_ONE','TOKEN_TWO'])
    async def test_password_change_revokes_only_the_preexisting_session_snapshot(self):
        await self.adapter.change_password('person','PRIVATE-new-password');self.auth.people['person'].refresh_tokens['new']='NEW_SIGN_IN';self.assertEqual(self.auth.revoked,[])
        callback,args=self.delayed.pop();callback(*args);self.assertEqual(self.auth.revoked,['TOKEN_ONE','TOKEN_TWO']);self.assertNotIn('NEW_SIGN_IN',self.auth.revoked)
    async def test_current_password_is_validated_without_returning_auth_provider_errors(self):
        with self.assertRaises(Exception) as caught:await self.adapter.verify('person','wrong')
        self.assertEqual(caught.exception.code,'invalid_password');await self.adapter.verify('person','fixture-password')
