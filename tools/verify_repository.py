"""Verify distributable source, asset consistency and private-data exclusions."""
from pathlib import Path
import hashlib,json,re,sys

root=Path(__file__).resolve().parents[1]
errors=[]
excluded={'.git','node_modules','__pycache__','build','dist'}
for file in root.rglob('*'):
    relative=file.relative_to(root)
    if any(part in excluded for part in relative.parts):continue
    if any(part in {'.storage','backups','work'} for part in relative.parts):
        errors.append(str(relative)+': private working data');continue
    if file.is_symlink():errors.append(str(relative)+': linked file');continue
    if not file.is_file():continue
    if file.suffix.lower() in {'.jks','.keystore','.protected','.pem','.key','.p12','.pfx','.sqlite','.db','.qcow2','.vdi','.apk','.log'} or file.name.startswith('.env'):
        errors.append(str(relative)+': private or generated file');continue
    if file.suffix.lower() in {'.png','.jar','.ico'}:continue
    try:content=file.read_text(encoding='utf-8')
    except UnicodeError:errors.append(str(relative)+': unexpected binary data');continue
    patterns=[r'gh[pousr]_[A-Za-z0-9]{25,}',r'github_pat_[A-Za-z0-9_]{20,}',r'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}',
              r'-----BEGIN [A-Z ]*PRIVATE KEY-----',r'https?://(?:192\.168\.\d+\.\d+|100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d+\.\d+)']
    if any(re.search(pattern,content) for pattern in patterns):errors.append(str(relative)+': possible private value; review locally')

frontend=root/'frontend'
for folder in [root/'custom_components/vautomate_studio/www',root/'android/app/src/main/assets/vautomate-customer']:
    for name in ['app.js','client.js','automations.js','index.html','studio.css','brand-long.svg','brand-short.svg']:
        if (folder/name).read_bytes()!=(frontend/name).read_bytes():errors.append(str(folder.relative_to(root)/name)+': stale frontend copy')

bundle=root/'installer/vautomate_installer'
manifest=json.loads((bundle/'payload.json').read_text())
source=root/'custom_components/vautomate_studio'
files={}
for file in source.rglob('*'):
    if not file.is_file() or '__pycache__' in file.parts or file.suffix=='.pyc':continue
    name='vautomate_studio/'+file.relative_to(source).as_posix()
    files[name]=hashlib.sha256(file.read_bytes()).hexdigest()
    destination=bundle/'payload'/name
    if not destination.is_file() or destination.read_bytes()!=file.read_bytes():errors.append(name+': stale installer payload')
if manifest['files']!=files:errors.append('Installer file manifest differs from source')
release=json.loads((root/'release.json').read_text())
if release['version']!=manifest['version']:errors.append('Release and installer versions differ')
if manifest['production_ready'] is not False or release['production_ready'] is not False:errors.append('Development source must not claim production certification')
if not (root/'repository.yaml').is_file():errors.append('Missing HAOS repository metadata')
if errors:
    print('Repository verification failed (values withheld):')
    print('\n'.join('- '+error for error in errors));sys.exit(1)
print('PASS: source and bundled assets match; no private files or recognizable credentials; development release gates retained.')
