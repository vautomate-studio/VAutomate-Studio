"""Unknown versions cannot silently acquire write access; storage is never guessed."""
from copy import deepcopy
import unittest
import test_engine as fixtures
from studio_product.compatibility import guard,status,CONTRACT_CHECKED_CORES,READ_OPERATIONS
from studio_product.document import normalize


class CompatibilityTest(unittest.TestCase):
    def test_only_exact_contract_versions_allow_writes(self):
        for version in CONTRACT_CHECKED_CORES:self.assertTrue(status(version)['writes_allowed']);guard(version,'command')
        for version in ['2026.10.5','2027.1.0','2026.11.0b1','2026.10.4.dev0','unknown']:
            self.assertFalse(status(version)['writes_allowed']);self.assertFalse(status(version)['certified'])
            for op in ['command','backups/approve','accounts/approve','pairing/begin','layout/publish','rooms/pause','replacements/approve','unregistered/new_write']:
                with self.assertRaises(fixtures.ProductError):guard(version,op)
    def test_read_surface_is_available_without_expanding_to_new_operations(self):
        for op in READ_OPERATIONS:guard('untested',op)


class DocumentTest(unittest.TestCase):
    def setUp(self):self.document={'revision':1,'layout':{'name':'Home','subtitle':'Welcome','rooms':[{'id':'living','name':'Living','entities':['light.old']}],'quick_actions':[]},'routines':[],'installation_id':'stable','future_optional_metadata':{'keep':'exactly'}}
    def test_legacy_is_migrated_as_a_copy_without_erasing_unknown_metadata(self):
        original=deepcopy(self.document);result=normalize(self.document);self.assertEqual(self.document,original);self.assertEqual(result['schema_version'],1);self.assertEqual(result['installation_id'],'stable');self.assertEqual(result['future_optional_metadata'],original['future_optional_metadata']);self.assertEqual(result,normalize(result))
    def test_newer_schema_is_rejected_and_source_kept(self):
        self.document['schema_version']=2;original=deepcopy(self.document)
        with self.assertRaises(ValueError):normalize(self.document)
        self.assertEqual(self.document,original)
    def test_malformed_root_and_non_finite_data_are_rejected(self):
        for change in [{'revision':True},{'revision':-1},{'schema_version':True},{'layout':{}},{'automations':[{}]},{'routines':[{}]},{'room_pauses':{'living':{'until':'later'}}},{'unknown':float('nan')}]:
            with self.assertRaises(ValueError):normalize({**self.document,**change})
        for value in [None,[],{},'invalid']:
            with self.assertRaises(ValueError):normalize(value)
    def test_missing_device_states_do_not_invalidate_stored_room_choices(self):self.assertEqual(normalize(self.document)['layout']['rooms'][0]['entities'],['light.old'])
    def test_deep_documents_and_duplicate_room_ids_are_rejected(self):
        value={};root=value
        for _ in range(45):value['nested']={};value=value['nested']
        with self.assertRaises(ValueError):normalize({**self.document,'extra':root})
        self.document['layout']['rooms']*=2
        with self.assertRaises(ValueError):normalize(self.document)
