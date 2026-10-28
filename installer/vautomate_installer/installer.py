"""Offline, manual installer. Only the Studio component directory is replaced."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import time
import urllib.request
import uuid

DOMAIN = 'vautomate_studio'
SUPPORTED = {'2026.9.4', '2026.10.2', '2026.10.4'}


class InstallError(Exception):
    pass


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def verified_payload(root):
    manifest = json.loads((root/'payload.json').read_text())
    files = manifest.get('files')
    if not isinstance(files, dict) or not files:
        raise InstallError('The bundled release has no verified files.')
    actual = set()
    for file in (root/'payload').rglob('*'):
        if file.is_symlink():
            raise InstallError('Linked release files are not allowed.')
        if file.is_file():
            actual.add(file.relative_to(root/'payload').as_posix())
    if actual != set(files):
        raise InstallError('The bundled release file list does not match.')
    for name, expected in files.items():
        parts = PurePosixPath(name).parts
        if '\\' in name or not parts or parts[0] != DOMAIN or '..' in parts or PurePosixPath(name).is_absolute():
            raise InstallError('The release contains an invalid path.')
        if hashlib.sha256((root/'payload'/name).read_bytes()).hexdigest() != expected:
            raise InstallError('The bundled release checksum does not match.')
    return manifest


def reject_links(root):
    if root.is_symlink() or any(p.is_symlink() for p in root.rglob('*')):
        raise InstallError('Linked installation paths need an installer to review them.')


class Supervisor:
    """No caller-controlled host, route, shell or download URL."""
    def __init__(self):
        self.token = os.environ.get('SUPERVISOR_TOKEN')
        if not self.token:
            raise InstallError('Start this installer through the HAOS app store.')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, method, route, body=None):
        allowed = {('GET','/core/info'), ('POST','/core/check'), ('POST','/core/restart'), ('GET','/core/api/vautomate_studio/v1/health'),
                   ('GET','/core/api/config/config_entries/entry'), ('POST','/core/api/config/config_entries/flow')}
        flow = route.removeprefix('/core/api/config/config_entries/flow/')
        if (method,route) not in allowed and not (method == 'POST' and route.startswith('/core/api/config/config_entries/flow/') and len(flow) == 32 and all(c in '0123456789abcdef' for c in flow)):
            raise InstallError('The installer refused an unsupported operation.')
        request = urllib.request.Request('http://supervisor'+route, method=method,
            headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'},
            data=json.dumps(body).encode() if body is not None else None)
        try:
            with self.opener.open(request, timeout=180) as response:
                value = json.load(response)
        except Exception:
            raise InstallError('The home server did not confirm the installer request.') from None
        if isinstance(value,dict) and value.get('result') == 'error':
            raise InstallError('The home server refused the installer request.')
        return value.get('data',value) if isinstance(value,dict) else value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise InstallError('Installer redirects are not allowed.')


class Installer:
    def __init__(self, bundle, config, data, api, *, sleep=time.sleep):
        self.bundle,self.config,self.data = map(Path,(bundle,config,data))
        self.api,self.sleep = api,sleep
        self.record = {}

    def note(self, phase, **values):
        self.record.update(phase=phase, **values)
        atomic_json(self.data/'install-status.json',self.record)
        print('VAutomate: '+phase, flush=True)

    def entries(self):
        entries = self.api.request('GET','/core/api/config/config_entries/entry')
        if not isinstance(entries,list):
            raise InstallError('The server returned an unsupported setup response.')
        return [e for e in entries if e.get('domain') == DOMAIN]

    def activate(self):
        for attempt in range(90):
            try:
                entries = self.entries()
                break
            except InstallError:
                if attempt == 89:
                    raise
                self.sleep(2)
        if not entries:
            flow = self.api.request('POST','/core/api/config/config_entries/flow',{'handler':DOMAIN,'show_advanced_options':False})
            if flow.get('type') == 'form' and flow.get('step_id') == 'user':
                flow_id = flow.get('flow_id','')
                if len(flow_id) != 32 or not all(c in '0123456789abcdef' for c in flow_id):
                    raise InstallError('The server returned an invalid setup identity.')
                flow = self.api.request('POST','/core/api/config/config_entries/flow/'+flow_id,{})
            if flow.get('type') != 'create_entry':
                raise InstallError('Studio setup needs installer attention. No extra entry was created.')
        for _ in range(30):
            entries = self.entries()
            if len(entries) == 1 and entries[0].get('state') == 'loaded':
                return
            self.sleep(2)
        raise InstallError('Studio was installed but did not confirm that it is running.')

    def install(self, *, allow_candidate=False, backup_confirmed=False):
        if not backup_confirmed:
            raise InstallError('Confirm an independently stored home backup before installation.')
        if not self.config.is_dir() or self.config.is_symlink():
            raise InstallError('The home configuration folder is not available.')
        manifest = verified_payload(self.bundle)
        if not manifest.get('production_ready') and not allow_candidate:
            raise InstallError('Customer release is blocked. This build is for isolated evaluation only.')
        info = self.api.request('GET','/core/info')
        if info.get('version') not in SUPPORTED:
            raise InstallError('This Core version has not passed the installer compatibility checks.')
        if self.data.is_symlink():
            raise InstallError('The installer data folder is linked.')
        self.data.mkdir(parents=True,exist_ok=True)
        self.record = {'release':manifest['version'],'production_ready':manifest['production_ready'],
                       'core_version':info['version'],'run_id':uuid.uuid4().hex,'started_at':int(time.time())}
        lock = self.data/'install.lock'
        try:
            descriptor = os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError:
            raise InstallError('Another installation may be active. Review its status before removing the installer lock.') from None
        os.close(descriptor)
        try:
            self.note('checking_home')
            self.api.request('POST','/core/check')
            parent = self.config/'custom_components'
            if parent.is_symlink():
                raise InstallError('The custom components folder is linked.')
            parent.mkdir(exist_ok=True)
            target = parent/DOMAIN
            reject_links(target)
            previous = self.config/('.studio_previous_'+self.record['run_id'])
            stage = self.config/('.studio_stage_'+self.record['run_id'])
            source = self.bundle/'payload'/DOMAIN
            identical = target.is_dir() and all((target/name.removeprefix(DOMAIN+'/')).is_file() and hashlib.sha256((target/name.removeprefix(DOMAIN+'/')).read_bytes()).hexdigest() == digest for name,digest in manifest['files'].items())
            if identical:
                existing={DOMAIN+'/'+p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
                identical=existing==set(manifest['files'])
            if not identical:
                if target.exists():
                    backup = self.data/'component-backups'/self.record['run_id']
                    backup.parent.mkdir(exist_ok=True)
                    shutil.copytree(target,backup)
                    self.record['component_backup'] = self.record['run_id']
                shutil.copytree(source,stage)
                self.note('installing_studio')
                if target.exists():
                    target.rename(previous)
                try:
                    stage.rename(target)
                    self.api.request('POST','/core/check')
                except Exception:
                    # Exact paths created by this run; never touch another component.
                    if target.is_dir():
                        shutil.rmtree(target)
                    if previous.exists():
                        previous.rename(target)
                    raise
                self.note('restarting_core')
                try:
                    self.api.request('POST','/core/restart')
                except InstallError:
                    # A timeout cannot prove that restart failed. Reconcile by reading.
                    self.note('waiting_for_core')
            self.note('connecting_studio')
            self.activate()
            health = self.api.request('GET','/core/api/vautomate_studio/v1/health')
            if health.get('bridge_version') != manifest['version'] or health.get('api_version') != 1 or health.get('initialized') is not True:
                raise InstallError('The running Studio service does not match the installed release. Review the restart before continuing.')
            if previous.exists():
                shutil.rmtree(previous)
            self.note('ready_for_onboarding',finished_at=int(time.time()),dashboard_path='/vautomate-studio/index.html',controls_enabled_automatically=False)
            return dict(self.record)
        except Exception:
            self.note('needs_installer_attention')
            raise
        finally:
            lock.unlink()


def main():
    try:
        options = json.loads(Path('/data/options.json').read_text())
        Installer(Path(__file__).parent,'/homeassistant','/data',Supervisor()).install(
            allow_candidate=options.get('allow_candidate') is True,
            backup_confirmed=options.get('independent_backup_confirmed') is True)
        print('Open /vautomate-studio/index.html on your home server. Sign in and choose Set up this home.')
    except Exception as error:
        print('VAutomate: '+(str(error) if isinstance(error,InstallError) else 'Installation needs attention; private details were withheld.'),flush=True)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
