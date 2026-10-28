"""Local installation inventory. No network access, tokens or remote deployment."""
from __future__ import annotations
from contextlib import closing
import argparse
import json
from pathlib import Path
import re
import sqlite3
import uuid

ALLOWED={'schema_version','installation_id','release','core_version','production_ready','layout_revision','room_count','device_count','offline_count','checks','automatic_updates','update_policy_scope','remote_support_enabled','checked_at'}


def validate(record):
    if not isinstance(record,dict) or set(record)-ALLOWED or record.get('schema_version')!=1:
        raise ValueError('Unsupported installation record; no personal fields are accepted.')
    if str(uuid.UUID(record.get('installation_id',''))) != record['installation_id']:
        raise ValueError('Invalid installation identity.')
    for key in ('release','core_version'):
        if not isinstance(record.get(key),str) or not re.fullmatch(r'[0-9][0-9A-Za-z.\-+]{1,49}',record[key]):
            raise ValueError('Invalid release identifier.')
    for key in ('checked_at','layout_revision','room_count','device_count','offline_count'):
        if type(record.get(key)) is not int or record[key]<0:
            raise ValueError('Invalid installation count or timestamp.')
    if record['room_count']>80 or record['device_count']>2000 or record['offline_count']>record['device_count']:
        raise ValueError('Installation counts exceed product limits.')
    for key in ('production_ready','automatic_updates','remote_support_enabled'):
        if type(record.get(key)) is not bool:
            raise ValueError('Missing installation policy result.')
    checks=record.get('checks')
    if not isinstance(checks,list) or len(checks)>30:
        raise ValueError('Invalid commissioning checks.')
    for check in checks:
        if not isinstance(check,dict) or set(check)!={'id','label','status'} or any(not isinstance(value,str) or len(value)>100 or any(ord(c)<32 for c in value) for value in check.values()):
            raise ValueError('Invalid commissioning check.')
    # Persist an explicit non-personal subset even if a future exporter grows.
    return {key:record[key] for key in ALLOWED if key in record}


def register(database, record):
    record=validate(record)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS homes (id TEXT PRIMARY KEY, checked INTEGER NOT NULL, document TEXT NOT NULL)')
        row=connection.execute('SELECT checked FROM homes WHERE id=?',(record['installation_id'],)).fetchone()
        if row and row[0]>record['checked_at']:
            raise ValueError('This record is older than the installed inventory entry.')
        connection.execute('INSERT INTO homes VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET checked=excluded.checked,document=excluded.document',
                           (record['installation_id'],record['checked_at'],json.dumps(record)))
        connection.commit()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--import-record',type=Path)
    options=parser.parse_args()
    if options.import_record:
        register(options.database,json.loads(options.import_record.read_text(encoding='utf-8')))
        print('Installation record stored locally. No remote action was performed.')
    else:
        if not options.database.exists():
            print('No homes registered yet.');return
        with closing(sqlite3.connect(options.database)) as connection:
            rows=connection.execute('SELECT document FROM homes ORDER BY id').fetchall()
        for row in rows:
            record=json.loads(row[0])
            print(f"{record['installation_id']} | Core {record['core_version']} | Studio {record['release']} | {record['room_count']} rooms | {record['offline_count']} offline | "+('certified' if record['production_ready'] else 'evaluation'))


if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,TypeError,json.JSONDecodeError):raise SystemExit('Invalid installation record; inventory unchanged.')
