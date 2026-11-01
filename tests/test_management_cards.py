"""Shared dashboard content and recovery references remain backend-enforced."""
from copy import deepcopy
import unittest
import test_engine as fixtures


class ManagementTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):fixtures.EngineTest.setUp(self)
    def layout(self,cards):return {**deepcopy(self.engine.document['layout']),'cards':cards,'cards_title':'Everyday essentials.','show_rooms':False}
    async def test_entity_card_add_resize_reorder_and_remove_are_persisted_shared(self):
        cards=[{'id':'light-card','kind':'entity','entity_id':'light.one','span':2,'title':'Evening pendant'},{'id':'room-card','kind':'room','room_id':'living','span':1}]
        await self.engine.publish(self.admin,self.layout(cards),2);self.assertEqual(self.engine.layout(self.member)['cards'],cards);self.assertFalse(self.engine.layout(self.member)['show_rooms']);self.assertEqual(len(self.adapter.saved),1)
        layout=self.layout([cards[1],{**cards[0],'span':3}]);await self.engine.publish(self.admin,layout,3);self.assertEqual(self.engine.layout(self.member)['cards'][1]['span'],3)
    async def test_card_only_entity_is_visible_and_obeys_permissions(self):
        self.adapter.states['sensor.extra']={'entity_id':'sensor.extra','state':'42','attributes':{}}
        await self.engine.publish(self.admin,self.layout([{'id':'reading','kind':'entity','entity_id':'sensor.extra','span':1}]),2);self.assertIn('sensor.extra',self.engine.managed());self.assertTrue(any(e['entity_id']=='sensor.extra' for e in self.engine.snapshot(self.member)))
        restricted=fixtures.Actor('restricted','Restricted',False,lambda i:i!='sensor.extra',lambda _:False);self.assertEqual(self.engine.layout(restricted)['cards'],[])
    async def test_members_cannot_publish_cards(self):
        with self.assertRaises(fixtures.ProductError):await self.engine.publish(self.member,self.layout([]),2)
    async def test_invalid_card_type_room_width_duplicates_and_fields_rejected(self):
        base={'id':'card','kind':'entity','entity_id':'light.one','span':1}
        for card in [{**base,'span':True},{**base,'span':4},{**base,'kind':'html'},{**base,'url':'external'},{'id':'room','kind':'room','room_id':'missing','span':1}]:
            with self.assertRaises(fixtures.ProductError):await self.engine.publish(self.admin,self.layout([card]),2)
        with self.assertRaises(fixtures.ProductError):await self.engine.publish(self.admin,self.layout([base,base]),2)
    async def test_room_or_control_removal_cannot_orphan_existing_rules(self):
        self.engine.document['routines']=[{'id':'routine','name':'Morning','actions':[{'entity_id':'light.one','action':'turn_on','data':{}}],'enabled':False}]
        layout=deepcopy(self.engine.document['layout']);layout['rooms'][0]['entities'].remove('light.one')
        with self.assertRaises(fixtures.ProductError) as raised:await self.engine.publish(self.admin,layout,2)
        self.assertEqual(raised.exception.code,'references_in_use');self.assertFalse(self.adapter.saved)
    async def test_room_removal_is_allowed_when_no_rule_or_card_depends_on_it(self):
        layout=deepcopy(self.engine.document['layout']);layout['rooms']=[];await self.engine.publish(self.admin,layout,2);self.assertEqual(self.engine.document['layout']['rooms'],[])
