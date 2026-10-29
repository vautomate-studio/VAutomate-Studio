"""Bundle reviewed local source, not downloaded code or household data."""
from pathlib import Path
import hashlib,json,shutil,zipfile

project=Path(__file__).resolve().parents[1]
app=project/'installer/vautomate_installer'
payload=app/'payload/vautomate_studio'
payload.mkdir(parents=True,exist_ok=True)
source=project/'custom_components/vautomate_studio'
files={}
for file in sorted(source.rglob('*'),key=lambda p:p.relative_to(source).as_posix()):
    if not file.is_file() or '__pycache__' in file.parts or file.suffix=='.pyc':continue
    if file.is_symlink():raise ValueError('Linked source file')
    # Git's declared text format and the Linux runtime both use LF. Normalize
    # before hashing so a Windows build verifies after a clean Git checkout.
    if file.suffix in {'.py','.json','.js','.html','.css','.svg'}:
        content=file.read_bytes()
        if b'\r\n' in content:file.write_bytes(content.replace(b'\r\n',b'\n'))
    relative=file.relative_to(source)
    destination=payload/relative;destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(file,destination)
    files['vautomate_studio/'+relative.as_posix()]=hashlib.sha256(file.read_bytes()).hexdigest()
for file in payload.rglob('*'):
    if file.is_file() and 'vautomate_studio/'+file.relative_to(payload).as_posix() not in files:
        raise ValueError('Unexpected old payload file; review it before rebuilding')
release=json.loads((project/'release.json').read_text())
if release['production_ready']:
    import subprocess,sys
    subprocess.run([sys.executable,str(project/'tools/check_release.py')],check=True)
manifest={'version':release['version'],'production_ready':release['production_ready'],'files':files,'manual_install_only':True}
(app/'payload.json').write_bytes((json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode('utf-8'))
output=project/'dist'/('VAutomate-Commissioning-Kit-'+release['version']+'.zip')
output.parent.mkdir(exist_ok=True)
def write(archive,file,name):
    content=file.read_bytes()
    if file.suffix in {'.py','.json','.js','.html','.css','.svg','.md','.yaml','.yml','.sh','.txt'} or file.name=='Dockerfile':
        content=content.replace(b'\r\n',b'\n')
    entry=zipfile.ZipInfo(str(name).replace('\\','/'),date_time=(1980,1,1,0,0,0))
    entry.create_system=3
    entry.external_attr=0o100644<<16
    # Stored entries avoid zlib-version variation. This small source kit has no
    # media payload; identical inputs produce identical bytes on every platform.
    entry.compress_type=zipfile.ZIP_STORED
    archive.writestr(entry,content)
with zipfile.ZipFile(output,'w',zipfile.ZIP_STORED) as archive:
    for file in sorted((project/'installer').rglob('*'),key=lambda p:p.relative_to(project/'installer').as_posix()):
        if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc':
            write(archive,file,file.relative_to(project/'installer'))
    write(archive,project/'tools/fleet_register.py','operations/fleet_register.py')
    write(archive,project/'release.json','operations/release-status.json')
print(json.dumps({'path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'files':len(files),'production_ready':release['production_ready']}))
