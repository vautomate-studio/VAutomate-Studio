import asyncio
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest
from test_engine import Actor,ProductError

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/household.py'
spec=importlib.util.spec_from_file_location('studio_product.household',path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)

def user(identity,role='member',owner=False):return {'id':identity,'name':identity,'owner':owner,'administrator':role=='administrator','role':role,'active':True,'local_only':False,'username':identity,'password_supported':True}

class Adapter:
    def __init__(self):
        self.people={'owner':user('owner','administrator',True),'admin':user('admin','administrator'),'member':user('member'),'viewer':user('viewer','viewer')};self.calls=[];self.fail=False;self.wait=None
    async def user(self,identity):
        if identity not in self.people:raise ProductError('account_missing','Gone')
        return deepcopy(self.people[identity])
    async def users(self):return deepcopy(list(self.people.values()))
    async def verify(self,identity,password):
        if password!='fixture-current-password':raise ProductError('invalid_password','Current password rejected')
    async def create(self,plan,password):
        self.calls.append(('create',plan['username']))
        if self.wait:await self.wait.wait()
        if self.fail:raise RuntimeError('PRIVATE new password and hash')
        self.people[plan['username']]=user(plan['username'],plan['role']);return deepcopy(self.people[plan['username']])
    async def update(self,identity,changes):self.calls.append(('update',identity));self.people[identity].update(changes)
    async def remove(self,identity):self.calls.append(('remove',identity));del self.people[identity]
    async def change_password(self,identity,password):self.calls.append(('password',identity))

class HouseholdTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.adapter=Adapter();self.clock=1000.;self.service=module.Household(self.adapter,clock=lambda:self.clock)
        self.owner=Actor('owner','Owner',True,lambda _:True,lambda _:True);self.admin=Actor('admin','Admin',True,lambda _:True,lambda _:True);self.member=Actor('member','Member',False,lambda _:True,lambda _:True)
    async def create_review(self,**change):return await self.service.preview(self.owner,{'kind':'create','name':'Family','username':'new_member','role':'member','local_only':False,**change})
    def approval(self,review,**change):return {'approval_nonce':review['approval_nonce'],'current_password':'fixture-current-password','new_password':'PRIVATE-new-password-long',**change}
    async def test_member_can_read_own_profile_but_not_administer(self):
        self.assertEqual((await self.service.me(self.member))['id'],'member')
        for call in [self.service.people(self.member),self.service.preview(self.member,{'kind':'create'}),self.service.approve(self.member,{})]:
            with self.assertRaises(ProductError):await call
        self.assertEqual(self.adapter.calls,[])
    async def test_inert_review_and_current_password_confirmation(self):
        review=await self.create_review();self.assertFalse(review['writes']);self.assertEqual(self.adapter.calls,[])
        with self.assertRaises(ProductError):await self.service.approve(self.owner,self.approval(review,current_password='wrong'))
        self.assertEqual(self.adapter.calls,[]);result=await self.service.approve(self.owner,self.approval(review));self.assertEqual(result['status'],'saved');self.assertNotIn('PRIVATE',repr(vars(self.service)))
    async def test_owner_and_self_protected_from_every_management_action(self):
        for identity in ['owner','admin']:
            for kind in ['remove','update','reset_password']:
                with self.assertRaises(ProductError):await self.service.preview(self.admin,{'kind':kind,'user_id':identity})
        self.assertEqual(self.adapter.calls,[])
    async def test_only_owner_can_reset_someone_elses_password(self):
        with self.assertRaises(ProductError):await self.service.preview(self.admin,{'kind':'reset_password','user_id':'member'})
        review=await self.service.preview(self.owner,{'kind':'reset_password','user_id':'member'});self.assertEqual((await self.service.approve(self.owner,self.approval(review)))['status'],'saved');self.assertEqual(self.adapter.calls,[('password','member')])
    async def test_duplicate_creation_does_not_create_or_reset_again(self):
        review=await self.create_review();result=await self.service.approve(self.owner,self.approval(review));self.assertEqual(await self.service.approve(self.owner,self.approval(review)),result);self.assertEqual(self.adapter.calls,[('create','new_member')])
    async def test_unknown_creation_result_is_consumed_not_leaked_or_retried(self):
        review=await self.create_review();self.adapter.fail=True;result=await self.service.approve(self.owner,self.approval(review));self.assertEqual(result['status'],'check_required');self.assertEqual(await self.service.approve(self.owner,self.approval(review)),result);self.assertEqual(len(self.adapter.calls),1);self.assertNotIn('PRIVATE',str(result))
    async def test_review_bound_to_actor_expiry_and_target_snapshot(self):
        review=await self.create_review()
        with self.assertRaises(ProductError):await self.service.approve(self.admin,self.approval(review))
        self.clock+=301
        with self.assertRaises(ProductError):await self.service.approve(self.owner,self.approval(review))
        review=await self.service.preview(self.owner,{'kind':'remove','user_id':'member'});self.adapter.people['member']['name']='Changed'
        with self.assertRaises(ProductError):await self.service.approve(self.owner,self.approval(review,confirmation='REMOVE'))
        self.assertEqual(self.adapter.calls,[])
    async def test_removal_requires_deliberate_confirmation(self):
        review=await self.service.preview(self.owner,{'kind':'remove','user_id':'member'})
        with self.assertRaises(ProductError):await self.service.approve(self.owner,self.approval(review))
        self.assertEqual((await self.service.approve(self.owner,self.approval(review,confirmation='REMOVE')))['status'],'saved');self.assertNotIn('member',self.adapter.people)
    async def test_revoked_admin_cannot_use_previous_review(self):
        review=await self.service.preview(self.admin,{'kind':'remove','user_id':'member'});self.adapter.people['admin']['administrator']=False
        with self.assertRaises(ProductError):await self.service.approve(self.admin,self.approval(review,confirmation='REMOVE'))
        self.assertEqual(self.adapter.calls,[])
    async def test_self_password_needs_current_password_and_strong_new_value(self):
        for payload in [{'current_password':'wrong','new_password':'PRIVATE-new-password-long'},{'current_password':'fixture-current-password','new_password':'short'}]:
            with self.assertRaises(ProductError):await self.service.own_password(self.member,payload)
        result=await self.service.own_password(self.member,{'current_password':'fixture-current-password','new_password':'PRIVATE-new-password-long'});self.assertTrue(result['sign_in_again']);self.assertEqual(self.adapter.calls,[('password','member')])
    async def test_new_passwords_cannot_be_silently_truncated_by_bcrypt(self):
        for value in ['a'*73,'界'*25,'a'*12+'\ud800']:
            with self.assertRaises(ProductError):await self.service.own_password(self.member,{'current_password':'fixture-current-password','new_password':value})
        self.assertEqual(self.adapter.calls,[])
    async def test_repeated_failed_password_verification_is_limited(self):
        for _ in range(5):
            with self.assertRaises(ProductError):await self.service.own_password(self.member,{'current_password':'wrong','new_password':'PRIVATE-new-password-long'})
        with self.assertRaises(ProductError) as caught:await self.service.own_password(self.member,{'current_password':'fixture-current-password','new_password':'PRIVATE-new-password-long'})
        self.assertEqual(caught.exception.code,'rate_limited');self.clock+=901
        await self.service.own_password(self.member,{'current_password':'fixture-current-password','new_password':'PRIVATE-new-password-long'})
    async def test_successful_administration_does_not_lock_out_an_installer(self):
        for index in range(8):
            review=await self.create_review(username='person_'+str(index));await self.service.approve(self.owner,self.approval(review))
        self.assertEqual(len(self.adapter.calls),8)
    async def test_view_only_role_is_explicit_and_unknown_roles_rejected(self):
        review=await self.create_review(role='viewer');result=await self.service.approve(self.owner,self.approval(review));self.assertEqual(result['user']['role'],'viewer')
        with self.assertRaises(ProductError):await self.create_review(role='system-generated')
    async def test_busy_changes_are_not_queued(self):
        first=await self.create_review();second=await self.create_review(username='second_member');self.adapter.wait=asyncio.Event();running=asyncio.create_task(self.service.approve(self.owner,self.approval(first)));await asyncio.sleep(0)
        with self.assertRaises(ProductError):await self.service.approve(self.owner,self.approval(second))
        self.adapter.wait.set();await running;self.assertEqual(len(self.adapter.calls),1)
    async def test_private_passwords_and_arbitrary_fields_never_belong_in_review(self):
        for change in [{'password':'PRIVATE'},{'group_ids':['system-admin']},{'url':'http://evil'},{'username':'Owner Name'},{'local_only':'true'}]:
            with self.assertRaises(ProductError):await self.create_review(**change)
    async def test_bounded_review_retention(self):
        for _ in range(100):await self.create_review()
        self.assertEqual(len(self.service.reviews),32)
