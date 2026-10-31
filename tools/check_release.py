"""Fail closed if someone attempts to promote a candidate without acceptance evidence."""
from pathlib import Path
import json,sys
from release_policy import audit
project=Path(__file__).resolve().parents[1]
release=json.loads((project/'release.json').read_text(encoding='utf-8'))
missing=audit(project,release)
if missing:
    print('PRODUCTION RELEASE BLOCKED. Candidate artifacts can be evaluated separately.')
    for name in missing:print('- '+name)
    sys.exit(2)
print('Acceptance records are present. Human release review remains required.')
