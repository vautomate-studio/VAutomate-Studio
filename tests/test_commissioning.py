from copy import deepcopy
import unittest
import test_engine as fixtures
from test_engine import Actor,ProductError
from studio_product.commissioning import status,suggest


class CommissioningTest(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.EngineTest();fixture.setUp()
        self.engine,self.admin,self.member=fixture.engine,fixture.admin,fixture.member
        self.engine.document['layout']['rooms']=[]
        self.discovery={'areas':[{'id':'living','name':'Living room'}],
            'devices':[{'id':'device','area_id':'living'}],
            'registry':[{'entity_id':'light.one','device_id':'device','area_id':None},
                        {'entity_id':'light.two','area_id':'living'},
                        {'entity_id':'sensor.temperature','area_id':'living'}]}
    def test_members_cannot_read_installation_identity_or_suggest_layout(self):
        for operation in [lambda:status(self.engine,self.member),lambda:suggest(self.engine,self.member,self.discovery)]:
            with self.assertRaises(ProductError):operation()
    def test_room_inheritance_and_entity_area_produce_inert_review(self):
        before=deepcopy(self.engine.document)
        result=suggest(self.engine,self.admin,self.discovery)
        self.assertEqual(result['layout']['rooms'][0]['entities'],['light.one','light.two'])
        self.assertFalse(result['writes']);self.assertFalse(result['devices_operated'])
        self.assertEqual(self.engine.document,before);self.assertEqual(self.engine.adapter.calls,[])
    def test_diagnostics_and_disabled_entities_are_not_suggested(self):
        self.discovery['registry'][0]['disabled']=True
        self.discovery['registry'][1]['diagnostic']=True
        self.assertEqual(suggest(self.engine,self.admin,self.discovery)['layout']['rooms'],[])
    def test_existing_rooms_cannot_be_replaced_by_auto_discovery(self):
        self.engine.document['layout']['rooms']=[{'id':'existing','name':'Existing','entities':['light.one']}]
        with self.assertRaises(ProductError):suggest(self.engine,self.admin,self.discovery)
    def test_installation_record_excludes_household_details(self):
        result=status(self.engine,self.admin)
        self.assertFalse(result['production_ready']);self.assertFalse(result['remote_support_enabled'])
        self.assertNotIn('entities',result);self.assertNotIn('users',result);self.assertNotIn('layout',result)
        self.assertEqual(len(result['installation_id']),36)


if __name__=='__main__':unittest.main()
