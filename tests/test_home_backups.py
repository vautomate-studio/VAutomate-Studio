import asyncio
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from test_engine import Actor, ProductError

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/home_backups.py'
spec=importlib.util.spec_from_file_location('studio_product.home_backups',path)
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)


class Adapter:
    def __init__(self):
        self.calls=[];self.valid=True;self.fail=False;self.wait=None;self.state='idle'
        self.item={'backup_id':'ab1234','name':'Home copy','date':'2026-10-29T10:00:00Z','size':128,
                   'protected':True,'home_included':True,'database_included':True,'core_version':'2026.10.4',
                   'app_count':2,'folders':['share'],'complete':True}
    async def authorize(self,identity):
        if not self.valid:raise ProductError('not_allowed','Revoked')
    async def status(self):return {'state':self.state,'can_create':True,'creation_includes':{'home':True,'database':True,'all_apps':True,'folders':['share']}}
    async def details(self,identity):return deepcopy(self.item)
    async def create(self,name,password):
        self.calls.append(('create',name))
        if self.wait:await self.wait.wait()
        if self.fail:raise RuntimeError('password=PRIVATE-RECOVERY-SECRET /private/path')
        return 'new1234'
    async def restore(self,item,password):
        self.calls.append(('restore',item['backup_id']))
        if self.fail:raise RuntimeError('password=PRIVATE-RECOVERY-SECRET /private/path')
    async def export(self,identity):self.calls.append(('export',identity));return 'encrypted-file'


class BackupTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.adapter=Adapter();self.clock=1000
        self.service=module.HomeBackups(self.adapter,clock=lambda:self.clock)
        self.admin=Actor('owner','Owner',True,lambda _:True,lambda _:True)
        self.other=Actor('other','Other admin',True,lambda _:True,lambda _:True)
        self.member=Actor('member','Member',False,lambda _:True,lambda _:True)
    async def preview(self,kind='create'):
        return await self.service.preview(self.admin,{'kind':kind,'backup_id':'ab1234'} if kind=='restore' else {'kind':kind,'name':'Home copy'})
    def approval(self,review,**extra):return {'approval_nonce':review['approval_nonce'],'password':'PRIVATE-RECOVERY-SECRET','password_saved':True,**extra}
    async def test_members_denied_every_operation(self):
        for operation in [self.service.status(self.member),self.service.preview(self.member,{'kind':'create'}),self.service.approve(self.member,{}),self.service.export(self.member,'ab1234'),self.service.prepare_download(self.member,'ab1234')]:
            with self.assertRaises(ProductError):await operation
        self.assertEqual(self.adapter.calls,[])
    async def test_preview_is_inert_and_no_secrets_are_retained(self):
        review=await self.preview();self.assertFalse(review['writes']);self.assertEqual(self.adapter.calls,[])
        result=await self.service.approve(self.admin,self.approval(review));self.assertEqual(result['status'],'started')
        self.assertNotIn('PRIVATE-RECOVERY-SECRET',repr(vars(self.service)));self.assertNotIn('password',json.dumps(result))
    async def test_password_and_acknowledgement_required(self):
        review=await self.preview()
        for change in [{'password':'short'},{'password_saved':False},{'password':12},{'password':'a'*257}]:
            with self.assertRaises(ProductError):await self.service.approve(self.admin,self.approval(review,**change))
        self.assertEqual(self.adapter.calls,[])
    async def test_review_is_bound_to_administrator_and_expiry(self):
        review=await self.preview()
        with self.assertRaises(ProductError):await self.service.approve(self.other,self.approval(review))
        self.clock+=301
        with self.assertRaises(ProductError):await self.service.approve(self.admin,self.approval(review))
    async def test_duplicate_approval_never_creates_another_backup(self):
        review=await self.preview();one=await self.service.approve(self.admin,self.approval(review));two=await self.service.approve(self.admin,self.approval(review));self.assertEqual(one,two);self.assertEqual(len(self.adapter.calls),1)
    async def test_unknown_result_is_consumed_not_retried_or_leaked(self):
        self.adapter.fail=True;review=await self.preview()
        result=await self.service.approve(self.admin,self.approval(review));self.assertEqual(result['status'],'check_required')
        self.assertEqual(await self.service.approve(self.admin,self.approval(review)),result)
        self.assertEqual(len(self.adapter.calls),1);self.assertNotIn('PRIVATE',json.dumps(result))
    async def test_restore_requires_fresh_typed_confirmation_and_independent_copy(self):
        review=await self.preview('restore')
        for values in [{},{'confirmation':'restore','independent_copy':True},{'confirmation':'RESTORE','independent_copy':False}]:
            with self.assertRaises(ProductError):await self.service.approve(self.admin,self.approval(review,**values))
        result=await self.service.approve(self.admin,self.approval(review,confirmation='RESTORE',independent_copy=True));self.assertEqual(result['status'],'requested');self.assertEqual(self.adapter.calls,[('restore','ab1234')])
    async def test_changed_restore_plan_requires_new_review(self):
        review=await self.preview('restore');self.adapter.item['size']=200
        with self.assertRaises(ProductError):await self.service.approve(self.admin,self.approval(review,confirmation='RESTORE',independent_copy=True))
        self.assertEqual(self.adapter.calls,[])
    async def test_permission_revocation_stops_dispatch_and_download(self):
        review=await self.preview();token=await self.service.prepare_download(self.admin,'ab1234');self.adapter.valid=False
        with self.assertRaises(ProductError):await self.service.approve(self.admin,self.approval(review))
        with self.assertRaises(ProductError):await self.service.download(token,'ab1234')
        self.assertEqual(self.adapter.calls,[])
    async def test_download_one_use_and_not_an_account_token(self):
        token=await self.service.prepare_download(self.admin,'ab1234');self.assertGreater(len(token),32)
        self.assertEqual(await self.service.download(token,'ab1234'),'encrypted-file')
        with self.assertRaises(ProductError):await self.service.download(token,'ab1234')
        self.assertEqual(self.adapter.calls,[('export','ab1234')])
    async def test_download_expiry_wrong_identity_and_path_rejected(self):
        token=await self.service.prepare_download(self.admin,'ab1234')
        with self.assertRaises(ProductError):await self.service.download(token,'other')
        token=await self.service.prepare_download(self.admin,'ab1234');self.clock+=301
        with self.assertRaises(ProductError):await self.service.download(token,'ab1234')
        for identity in ['../auth','a/b','http://evil','a'*129]:
            with self.assertRaises(ProductError):await self.service.prepare_download(self.admin,identity)
        self.assertEqual(self.adapter.calls,[])
    async def test_parallel_requests_are_not_queued(self):
        first=await self.preview();second=await self.preview();self.adapter.wait=asyncio.Event()
        running=asyncio.create_task(self.service.approve(self.admin,self.approval(first)));await asyncio.sleep(0)
        with self.assertRaises(ProductError):await self.service.approve(self.admin,self.approval(second))
        self.adapter.wait.set();await running;self.assertEqual(len(self.adapter.calls),1)
    async def test_cancelled_dispatch_is_not_repeated(self):
        review=await self.preview();self.adapter.wait=asyncio.Event();running=asyncio.create_task(self.service.approve(self.admin,self.approval(review)));await asyncio.sleep(0);running.cancel()
        with self.assertRaises(asyncio.CancelledError):await running
        self.assertEqual((await self.service.approve(self.admin,self.approval(review)))['status'],'check_required');self.assertEqual(len(self.adapter.calls),1)
    async def test_bounded_reviews_and_receipts(self):
        for _ in range(100):await self.preview()
        self.assertEqual(len(self.service.reviews),32)
    async def test_backup_without_home_cannot_be_restored(self):
        self.adapter.item['home_included']=False
        with self.assertRaises(ProductError):await self.preview('restore')
    async def test_unknown_payloads_rejected(self):
        with self.assertRaises(ProductError):await self.service.preview(self.admin,{'kind':'create','url':'http://evil'})
        with self.assertRaises(ProductError):await self.service.preview(self.admin,{'kind':'delete'})
        with self.assertRaises(ProductError):await self.service.approve(self.admin,{'approval_nonce':'x','path':'../auth'})
