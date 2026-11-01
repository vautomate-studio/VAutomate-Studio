import asyncio
from copy import deepcopy
from types import SimpleNamespace as NS
import unittest
import test_engine as f
from studio_product.remote_access import RemoteAccess,HARemote,login_url,node_view,SLUG

class Adapter:
    def __init__(self):
        self.calls=[];self.revoked=False;self.hold=None;self.fail=False
        self.report={'supported':True,'installed':False,'connected':False,'app_state':'not_installed'}
    async def authorize(self,user):
        if self.revoked:raise f.ProductError('not_allowed','Revoked')
    async def status(self,user):return deepcopy(self.report)
    async def journal(self,stage):self.calls.append(('journal',stage))
    async def install(self):
        self.calls.append(('install',))
        if self.hold:await self.hold.wait()
        if self.fail:raise RuntimeError('PRIVATE exception')
    async def start(self):self.calls.append(('start',));self.report.update(installed=True,app_state='started')
    async def stop(self):self.calls.append(('stop',));self.report['app_state']='stopped'
    async def signin(self,user):self.calls.append(('signin',));return {'url':'https://login.tailscale.com/a/inert-test-only'}

class RemoteTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        fixture=f.EngineTest();fixture.setUp();self.engine=fixture.engine;self.owner=fixture.admin;self.member=fixture.member;self.adapter=Adapter();self.remote=RemoteAccess(self.engine,self.adapter)
    async def approve(self):
        plan=await self.remote.preview(self.owner,{})
        return await self.remote.enable(self.owner,{'approval_nonce':plan['approval_nonce'],'confirmed':True})
    async def test_every_operation_denies_member(self):
        for method,payload in [('status',None),('preview',{}),('enable',{}),('signin',{}),('disable',{'confirmed':True})]:
            with self.assertRaises(f.ProductError):await (getattr(self.remote,method)(self.member) if payload is None else getattr(self.remote,method)(self.member,payload))
        self.assertEqual(self.adapter.calls,[])
    async def test_review_is_inert_and_bound_to_owner(self):
        plan=await self.remote.preview(self.owner,{})
        self.assertFalse(plan['writes']);self.assertEqual(self.adapter.calls,[])
        other=f.Actor('other','Other admin',True,lambda _:True,lambda _:True)
        with self.assertRaises(f.ProductError):await self.remote.enable(other,{'approval_nonce':plan['approval_nonce'],'confirmed':True})
        with self.assertRaises(f.ProductError):await self.remote.enable(self.owner,{'approval_nonce':plan['approval_nonce'],'confirmed':False})
    async def test_install_runs_in_background_and_nonce_is_one_use(self):
        self.adapter.hold=asyncio.Event();result=await self.approve();self.assertTrue(result['accepted']);await asyncio.sleep(0)
        self.assertEqual(self.remote.phase,'installing');self.assertEqual(self.adapter.calls[0],('journal','requested'))
        self.adapter.hold.set();await self.remote.task;self.assertEqual(self.remote.phase,'ready');self.assertIn(('start',),self.adapter.calls)
    async def test_revoked_admin_does_not_start_a_network(self):
        self.adapter.hold=asyncio.Event();await self.approve();await asyncio.sleep(0);self.adapter.revoked=True;self.adapter.hold.set();await self.remote.task
        self.assertNotIn(('start',),self.adapter.calls);self.assertEqual(self.remote.phase,'attention')
    async def test_install_failure_is_redacted_not_retried(self):
        self.adapter.fail=True;await self.approve();await self.remote.task
        self.assertNotIn('PRIVATE',str(self.remote.failure));self.assertEqual(self.adapter.calls.count(('install',)),1);self.assertEqual(self.remote.phase,'attention')
    async def test_disable_is_explicit_and_keeps_account(self):
        with self.assertRaises(f.ProductError):await self.remote.disable(self.owner,{})
        result=await self.remote.disable(self.owner,{'confirmed':True});self.assertTrue(result['account_kept']);await self.remote.task;self.assertEqual(self.remote.phase,'disabled')
    async def test_read_only_never_installs_or_signs_in(self):
        self.engine.controls=False
        for name,args in [('preview',{}),('signin',{}),('enable',{}),('disable',{'confirmed':True})]:
            with self.assertRaises(f.ProductError):await getattr(self.remote,name)(self.owner,args)
        self.assertEqual(self.adapter.calls,[])
    async def test_unexpected_signin_url_is_rejected(self):
        self.adapter.report.update(installed=True,app_state='started')
        async def wrong(_):return {'url':'https://other.test/a/secret'}
        self.adapter.signin=wrong
        with self.assertRaises(f.ProductError):await self.remote.signin(self.owner,{})
    def test_login_url_is_strict(self):
        self.assertEqual(login_url('https://login.tailscale.com/a/inert'), 'https://login.tailscale.com/a/inert')
        for value in ['http://login.tailscale.com/a/inert','https://login.tailscale.com.other.test/a/inert','https://user@login.tailscale.com/a/inert','https://login.tailscale.com/a/inert?redirect=other','javascript:alert(1)']:
            self.assertIsNone(login_url(value))
    def test_verified_status_never_exports_identity_or_keys(self):
        raw={'Status':'Running','IPv4':'100.100.2.10','Profile':{'Name':'PRIVATE'},'AuthKey':'PRIVATE'}
        view=node_view(raw,8123);self.assertTrue(view['connected']);self.assertEqual(view['remote_address'],'http://' + raw['IPv4'] + ':8123');self.assertNotIn('PRIVATE',str(view))
        raw['KeyExpired']=True;self.assertFalse(node_view(raw,8123)['connected']);self.assertIsNone(node_view(raw,8123)['remote_address'])
        raw.update(KeyExpired=False,IPv4='8.8.8.8');self.assertFalse(node_view(raw,8123)['connected'])

class AdapterTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.adapter=HARemote.__new__(HARemote);self.calls=[];self.installed=False;self.options={'accept_dns':True,'accept_routes':False,'advertise_routes':[],'advertise_exit_node':False,'share_homeassistant':'disabled','taildrop':False,'taildrive':{'config':False}}
        async def supervisor(path,method='get',payload=None,**kwargs):
            self.calls.append((path,method,deepcopy(payload)))
            if path=='/addons':return {'addons':[{'slug':SLUG}] if self.installed else []}
            if path=='/store':return {'addons':[{'slug':SLUG}],'repositories':[]}
            if path.endswith('/install'):self.installed=True
            if path.endswith('/info'):return {'state':'stopped','options':deepcopy(self.options)}
            if path.endswith('/options') and payload.get('options'):self.options=payload['options']
            return {}
        self.adapter.supervisor=supervisor
    async def test_new_install_private_options_and_boot(self):
        await self.adapter.install();self.assertFalse(self.options['accept_dns']);self.assertFalse(self.options['advertise_routes']);self.assertEqual(self.options['share_homeassistant'],'disabled')
        self.assertIn(('/addons/'+SLUG+'/options','post',{'boot':'auto','watchdog':True,'auto_update':False}),self.calls)
    async def test_existing_advanced_settings_are_never_overwritten(self):
        self.installed=True;self.options['share_homeassistant']='funnel'
        with self.assertRaises(f.ProductError):await self.adapter.install()
        self.assertFalse(any(method=='post' for _,method,_ in self.calls))
    async def test_arbitrary_ingress_paths_are_rejected(self):
        with self.assertRaises(f.ProductError):await self.adapter.web('owner','POST','arbitrary')
