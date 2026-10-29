"""Verify a rebuilt commissioning archive against its reviewed cross-platform hash."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
release=json.loads((root/'release.json').read_text(encoding='utf-8'))
record=json.loads((root/'evidence/source-kit.json').read_text(encoding='utf-8'))
artifact=root/'dist'/('VAutomate-Commissioning-Kit-'+release['version']+'.zip')
if record['version']!=release['version'] or not artifact.is_file():
    raise SystemExit('Source kit or reviewed release hash is missing for this version.')
if hashlib.sha256(artifact.read_bytes()).hexdigest()!=record['sha256']:
    raise SystemExit('Source kit bytes differ from the reviewed build. Do not distribute this archive.')
print('PASS: commissioning source kit matches its reviewed cross-platform SHA-256.')
