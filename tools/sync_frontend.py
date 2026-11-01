"""Stamp release-specific asset URLs and synchronize the reviewed frontends."""
from pathlib import Path
import json,re,shutil
ASSETS=['app.js','client.js','onboarding.js','automations.js','index.html','studio.css','brand-long.svg','brand-short.svg']
def sync(project):
    version=json.loads((project/'release.json').read_text())['version']
    for entry in ['index.html','showroom.html']:
        file=project/'frontend'/entry;html=file.read_text(encoding='utf-8')
        html=re.sub(r' data-build="[^"]*"','',html).replace('<html lang="en"','<html lang="en" data-build="'+version+'"')
        for name in ASSETS+['showroom.js']:
            html=re.sub(r'((?:src|href)=")'+re.escape(name)+r'(?:\?[^"<>]*)?"',lambda match:match[1]+name+'?v='+version+'"',html)
        file.write_text(html,encoding='utf-8',newline='\n')
    for name in ASSETS:
        source=project/'frontend'/name;source.write_bytes(source.read_bytes().replace(b'\r\n',b'\n'))
        for folder in ['custom_components/vautomate_studio/www','android/app/src/main/assets/vautomate-customer']:
            shutil.copyfile(source,project/folder/name)
if __name__=='__main__':sync(Path(__file__).resolve().parents[1])
