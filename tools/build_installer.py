"""Bundle reviewed local source, not downloaded code or household data."""
from pathlib import Path
import hashlib,json,shutil,zipfile

project=Path(__file__).resolve().parents[1]
app=project/'installer/vautomate_installer'
payload=app/'payload/vautomate_studio'
payload.mkdir(parents=True,exist_ok=True)
source=project/'custom_components/vautomate_studio'
files={}
for file in source.rglob('*'):
    if not file.is_file() or '__pycache__' in file.parts or file.suffix=='.pyc':continue
    if file.is_symlink():raise ValueError('Linked source file')
    relative=file.relative_to(source)
    destination=payload/relative;destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(file,destination)
    files['vautomate_studio/'+relative.as_posix()]=hashlib.sha256(file.read_bytes()).hexdigest()
for file in payload.rglob('*'):
    if file.is_file() and 'vautomate_studio/'+file.relative_to(payload).as_posix() not in files:
        raise ValueError('Unexpected old payload file; review it before rebuilding')
manifest={'version':'0.3.0-dev.4','production_ready':False,'files':files,'manual_install_only':True}
(app/'payload.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
output=project/'dist/VAutomate-Commissioning-Kit-0.3.0-dev.4.zip'
output.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
    for file in (project/'installer').rglob('*'):
        if file.is_file() and '__pycache__' not in file.parts and file.suffix!='.pyc':
            archive.write(file,file.relative_to(project/'installer'))
with zipfile.ZipFile(output,'a',zipfile.ZIP_DEFLATED) as archive:
    archive.write(project/'tools/fleet_register.py','operations/fleet_register.py')
    archive.write(project/'release.json','operations/release-status.json')
print(json.dumps({'path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'files':len(files),'production_ready':False}))
