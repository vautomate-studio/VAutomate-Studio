"""Replacement never dispatches a device action or changes external configuration."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest
import test_engine as fixtures
from studio_product.rule_templates import prepare

path=Path(__file__).resolve().parents[1]/'custom_components/vautomate_studio/replacement.py'
spec=importlib.util.spec_from_file_location('studio_product.replacement',path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)


class ReplacementTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        fixtures.EngineTest.setUp(self);self.allowed=True
        async def authorize(identity):
            if not self.allowed:raise fixtures.ProductError('not_allowed','Revoked')
        self.service=module.Replacement(self.engine,authorize)
        self.adapter.states['light.new']=deepcopy(self.adapter.states['light.one']);self.adapter.states['light.new']['entity_id']='light.new'
        self.adapter.states['binary_sensor.presence']={'entity_id':'binary_sensor.presence','state':'off','attributes':{'device_class':'occupancy'}}
        self.engine.document['layout']['rooms'][0]['entities'].append('binary_sensor.presence')
        rule,origin=prepare(self.engine,self.admin,'room_presence',{'room_id':'living','targets':{'sensor':'binary_sensor.presence','lights':['light.one']},'pause_modes':[]});rule['enabled']=True
        self.engine.document['automations']=[{'rule':rule,'origin':origin,'owner_id':'owner','approval_keys':['old-key']}]
        self.engine.document['routines']=[{'id':'morning','name':'Morning','time':'08:00','days':[1],'enabled':True,'actions':[{'entity_id':'light.one','action':'turn_on','data':{}}],'owner_id':'owner','origin':{'bundle_id':'custom','bundle_version':1,'customized':False}}]
    async def review(self,**change):return await self.service.preview(self.admin,{'replacements':[{'from':'light.one','to':'light.new'}],'revision':2,**change})
    def approval(self,review,**change):return {'approval_nonce':review['approval_nonce'],'confirmed':True,'external_scope_ack':True,**change}
    async def test_review_is_inert_and_lists_all_affected_references(self):
        before=deepcopy(self.engine.document);review=await self.review();self.assertEqual(self.engine.document,before);self.assertFalse(self.adapter.saved);self.assertFalse(self.adapter.calls);self.assertFalse(review['operates_devices']);self.assertEqual(review['changes']['rooms'][0]['id'],'living');self.assertEqual(review['changes']['schedules'][0]['id'],'morning');self.assertEqual(len(review['changes']['automations']),1)
    async def test_status_respects_entity_read_permissions_even_for_administrators(self):
        restricted=fixtures.Actor('restricted','Restricted',True,lambda i:i=='light.one',lambda _:False)
        result=await self.service.status(restricted);self.assertEqual([e['entity_id'] for e in result['entities']],['light.one'])
    async def test_approval_is_single_commit_and_affected_rules_stay_paused(self):
        review=await self.review();await self.service.approve(self.admin,self.approval(review));self.assertEqual(len(self.adapter.saved),1);self.assertFalse(self.adapter.calls);self.assertNotIn('light.one',self.engine.managed());self.assertIn('light.new',self.engine.managed());self.assertFalse(self.engine.document['routines'][0]['enabled']);self.assertFalse(self.engine.document['automations'][0]['rule']['enabled']);self.assertEqual(self.engine.document['automations'][0]['owner_id'],'owner');self.assertTrue(self.engine.document['automations'][0]['origin']['customized']);self.assertEqual(self.engine.document['revision'],3)
    async def test_duplicate_approval_does_not_save_or_operate_twice(self):
        review=await self.review();payload=self.approval(review);await self.service.approve(self.admin,payload);await self.service.approve(self.admin,payload);self.assertEqual(len(self.adapter.saved),1);self.assertFalse(self.adapter.calls)
        restarted=module.Replacement(self.engine,self.service.authorize);self.assertEqual((await restarted.approve(self.admin,payload))['status'],'saved');self.assertEqual(len(self.adapter.saved),1)
    async def test_disk_failure_keeps_old_home_and_review_can_be_retried(self):
        before=deepcopy(self.engine.document);review=await self.review();self.adapter.disk_failure=True
        with self.assertRaises(OSError):await self.service.approve(self.admin,self.approval(review))
        self.assertEqual(self.engine.document,before);self.adapter.disk_failure=False;await self.service.approve(self.admin,self.approval(review));self.assertEqual(self.engine.document['revision'],3)
    async def test_member_revoked_admin_and_another_actor_cannot_approve(self):
        review=await self.review()
        with self.assertRaises(fixtures.ProductError):await self.service.preview(self.member,{})
        with self.assertRaises(fixtures.ProductError):await self.service.approve(self.member,self.approval(review))
        another=fixtures.Actor('another','Another',True,lambda _:True,lambda _:True)
        with self.assertRaises(fixtures.ProductError):await self.service.approve(another,self.approval(review))
        self.allowed=False
        with self.assertRaises(fixtures.ProductError):await self.service.approve(self.admin,self.approval(review))
        self.assertFalse(self.adapter.saved)
    async def test_expired_or_revision_conflicted_review_cannot_commit(self):
        review=await self.review();self.adapter.clock+=301
        with self.assertRaises(fixtures.ProductError):await self.service.approve(self.admin,self.approval(review))
        review=await self.review();self.engine.document['revision']+=1
        with self.assertRaises(fixtures.ProductError):await self.service.approve(self.admin,self.approval(review))
        self.assertFalse(self.adapter.saved)
    async def test_both_deliberate_acknowledgements_are_required(self):
        review=await self.review()
        for values in [{'confirmed':False},{'external_scope_ack':False}]:
            with self.assertRaises(fixtures.ProductError):await self.service.approve(self.admin,self.approval(review,**values))
        self.assertFalse(self.adapter.saved)
    async def test_same_entity_cycles_merges_foreign_types_and_duplicate_sources_rejected(self):
        for pairs in [[{'from':'light.one','to':'light.one'}],[{'from':'light.one','to':'light.two'}],[{'from':'light.one','to':'cover.blind'}],[{'from':'missing.old','to':'light.new'}],[{'from':'light.one','to':'light.new'}]*2]:
            with self.assertRaises(fixtures.ProductError):await self.review(replacements=pairs)
    async def test_new_device_must_be_connected_and_support_existing_actions(self):
        self.adapter.states['light.new']['state']='unavailable'
        with self.assertRaises(fixtures.ProductError):await self.review()
        self.adapter.states['light.new']['state']='off';self.adapter.has_service=lambda domain,action:False
        with self.assertRaises(fixtures.ProductError):await self.review()
    async def test_missing_original_can_be_replaced_and_is_disclosed(self):
        del self.adapter.states['light.one'];review=await self.review();self.assertTrue(review['missing_original']);await self.service.approve(self.admin,self.approval(review));self.assertIn('light.new',self.engine.managed())
    async def test_reading_class_and_unit_changes_rejected(self):
        self.adapter.states['sensor.new']={'entity_id':'sensor.new','state':'75','attributes':{'unit_of_measurement':'°F'}}
        with self.assertRaises(fixtures.ProductError):await self.review(replacements=[{'from':'sensor.temperature','to':'sensor.new'}])
    async def test_capability_change_or_original_disappearance_requires_new_review(self):
        review=await self.review();self.adapter.states['light.new']['attributes']['supported_color_modes']=['onoff']
        with self.assertRaises(fixtures.ProductError):await self.service.approve(self.admin,self.approval(review))
        review=await self.review();del self.adapter.states['light.one']
        with self.assertRaises(fixtures.ProductError):await self.service.approve(self.admin,self.approval(review))
        self.assertFalse(self.adapter.saved)
    async def test_only_semantic_references_are_rewritten(self):
        value={'name':'light.one','entity_id':'light.one','pause_modes':['input_boolean.sleep'],'data':{'source':'light.one'}}
        result=module.remap(value,{'light.one':'light.new','input_boolean.sleep':'input_boolean.night'});self.assertEqual(result,{'name':'light.one','entity_id':'light.new','pause_modes':['input_boolean.night'],'data':{'source':'light.one'}});self.assertEqual(value['entity_id'],'light.one')
    async def test_unrelated_rule_and_runtime_metadata_are_preserved(self):
        unrelated={'id':'other','name':'Other','time':'09:00','days':[1],'enabled':True,'actions':[{'entity_id':'light.two','action':'turn_off','data':{}}]};self.engine.document['routines'].append(deepcopy(unrelated));self.engine.document['routine_runs']={'other':'already-ran'}
        review=await self.review();await self.service.approve(self.admin,self.approval(review));self.assertEqual(self.engine.document['routines'][1],unrelated);self.assertEqual(self.engine.document['routine_runs'],{'other':'already-ran'})
