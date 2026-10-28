from contextlib import closing
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
import uuid

spec=importlib.util.spec_from_file_location('fleet',Path(__file__).resolve().parents[1]/'tools/fleet_register.py')
fleet=importlib.util.module_from_spec(spec);spec.loader.exec_module(fleet)


class FleetTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.database=Path(self.temp.name)/'fleet.sqlite'
        self.record={'schema_version':1,'installation_id':str(uuid.uuid4()),'release':'0.3.0-dev.1','core_version':'2026.10.4',
            'production_ready':False,'layout_revision':1,'room_count':2,'device_count':12,'offline_count':0,
            'checks':[],'automatic_updates':False,'remote_support_enabled':False,'checked_at':1000}
    def test_same_home_is_updated_not_duplicated(self):
        fleet.register(self.database,self.record);self.record['checked_at']+=1;fleet.register(self.database,self.record)
        with closing(sqlite3.connect(self.database)) as db:self.assertEqual(db.execute('SELECT count(*) FROM homes').fetchone()[0],1)
    def test_old_record_cannot_overwrite_newer_status(self):
        fleet.register(self.database,self.record);self.record['checked_at']-=1
        with self.assertRaises(ValueError):fleet.register(self.database,self.record)
    def test_tokens_and_unknown_fields_are_rejected_before_database_write(self):
        self.record['access_token']='NEVER_STORE'
        with self.assertRaises(ValueError):fleet.register(self.database,self.record)
        self.assertFalse(self.database.exists())
    def test_boolean_counts_are_not_valid_numbers(self):
        self.record['room_count']=True
        with self.assertRaises(ValueError):fleet.validate(self.record)
