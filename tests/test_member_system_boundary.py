import unittest
import test_engine as f


class MemberSystemBoundary(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        fixture=f.EngineTest();fixture.setUp()
        self.engine=fixture.engine;self.adapter=fixture.adapter
        self.member=fixture.member;self.admin=fixture.admin
        self.adapter.is_system_entity=lambda entity:entity=='light.two'
        self.adapter.states['input_boolean.service_mode']={'entity_id':'input_boolean.service_mode','state':'off','attributes':{}}
        self.engine.document['layout']['rooms'][0]['entities'].append('input_boolean.service_mode')

    async def test_member_cannot_read_or_command_published_system_control(self):
        visible={s['entity_id'] for s in self.engine.snapshot(self.member)}
        self.assertNotIn('light.two',visible)
        self.assertNotIn('input_boolean.service_mode',visible)
        self.assertNotIn('light.two',self.engine.layout(self.member)['rooms'][0]['entities'])
        with self.assertRaises(f.ProductError) as caught:
            self.engine.entity(self.member,'light.two',control=True)
        self.assertEqual(caught.exception.code,'not_allowed')
        self.assertEqual(self.adapter.calls,[])

    async def test_administrator_keeps_system_access(self):
        snapshot={s['entity_id']:s for s in self.engine.snapshot(self.admin)}
        self.assertTrue(snapshot['light.two']['system'])
        self.assertIn('input_boolean.service_mode',snapshot)
        self.assertEqual(self.engine.entity(self.admin,'light.two',control=True)['entity_id'],'light.two')

    async def test_room_master_does_not_dispatch_to_system_control(self):
        await self.engine.command(self.member,{'request_id':'member-room-system-check','expires_at':1015,'room_id':'living','category':'light'})
        self.assertEqual([call[1] for call in self.adapter.calls],['light.one'])

    async def test_only_curated_home_mode_is_available_to_member(self):
        self.engine.document['layout']['quick_actions'].append({'entity_id':'input_boolean.service_mode','label':'Approved home mode'})
        self.assertIn('input_boolean.service_mode',{s['entity_id'] for s in self.engine.snapshot(self.member)})
        self.assertEqual(self.engine.entity(self.member,'input_boolean.service_mode',control=True)['state'],'off')
        self.assertEqual(self.adapter.calls,[])
