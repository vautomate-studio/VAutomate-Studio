"""Fail closed if someone attempts to promote a candidate without acceptance evidence."""
from pathlib import Path
import json,sys
project=Path(__file__).resolve().parents[1]
release=json.loads((project/'release.json').read_text(encoding='utf-8'))
missing=[]
for name in ['engine-results.json','browser-results.json']:
    file=project/'evidence'/name
    if not file.exists() or json.loads(file.read_text(encoding='utf-8')).get('status')!='passed':missing.append(name)
for name,gate in release['required_acceptance'].items():
    evidence=gate.get('evidence')
    if gate['status']!='passed' or not evidence:missing.append(name);continue
    file=(project/evidence).resolve()
    if not file.is_relative_to(project.resolve()) or not file.is_file():missing.append(name+': evidence missing')
catalogue=json.loads((project/'catalogue/devices.json').read_text(encoding='utf-8'))
if not catalogue['approved_devices']:missing.append('approved device catalogue is empty')
if not release['certified_core_versions']:missing.append('no Core versions certified')
if missing:
    print('PRODUCTION RELEASE BLOCKED. Candidate artifacts can be evaluated separately.')
    for name in missing:print('- '+name)
    sys.exit(2)
print('Acceptance records are present. Human release review remains required.')
