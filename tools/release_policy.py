"""Evidence checks for deliberate production promotion; never an automatic release."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re

REQUIRED_GATES=frozenset({'isolated_haos_runtime','core_upgrade_and_compatibility','supervisor_update_and_backup_restore','approved_hardware_matrix','android_12_through_current_physical_devices','camera_live_video_and_remote_connectivity','pairing_and_device_replacement','security_review_and_customer_authorization','notification_delivery_and_recovery','installer_handover_and_account_recovery','complex_visual_automation_builder','manual_update_policy_enforcement','native_occupancy_blueprint_validation_and_creation_binding','commercial_installer_and_first_home'})
PHYSICAL_DEVICE_GATES=frozenset({'approved_hardware_matrix','android_12_through_current_physical_devices','camera_live_video_and_remote_connectivity','pairing_and_device_replacement','notification_delivery_and_recovery','native_occupancy_blueprint_validation_and_creation_binding'})
REQUIRED_GATES=REQUIRED_GATES|{'data_migration_and_forward_version_safety','installer_distribution_and_signed_artifacts'}


def runtime_digest(root):
    root=Path(root).resolve();sources=[root/'custom_components/vautomate_studio',root/'android/app/src']
    digest=hashlib.sha256()
    files=[]
    for source in sources:
        if not source.is_dir() or source.is_symlink() or not source.resolve().is_relative_to(root):raise ValueError('Missing or linked runtime source')
        files.extend(source.rglob('*'))
    files.extend(root/'installer/vautomate_installer'/name for name in ['installer.py','Dockerfile','config.yaml'] if (root/'installer/vautomate_installer'/name).exists())
    files.extend(root/name for name in ['android/app/build.gradle','android/build.gradle','android/settings.gradle','android/tools/build-unsigned.py','android/vendor/dependencies.json'] if (root/name).exists())
    for file in sorted(files,key=lambda p:p.relative_to(root).as_posix()):
        if '__pycache__' in file.parts or file.suffix=='.pyc':continue
        if file.is_symlink():raise ValueError('Linked runtime source')
        if file.is_file():
            content=file.read_bytes()
            if file.suffix in {'.py','.java','.json','.xml','.js','.html','.css','.svg','.yaml','.gradle'} or file.name=='Dockerfile':content=content.replace(b'\r\n',b'\n')
            digest.update(file.relative_to(root).as_posix().encode()+b'\0'+content+b'\0')
    return digest.hexdigest()


def read(root,relative,expected=None):
    if not isinstance(relative,str) or not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:raise ValueError('Invalid evidence path')
    path=root/relative
    if not path.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in [path,*path.parents] if p!=root.parent):raise ValueError('Linked or external evidence')
    if not path.is_file() or path.stat().st_size>2*1024**2:raise ValueError('Missing or oversized evidence')
    content=path.read_bytes()
    if expected is not None and (not isinstance(expected,str) or not re.fullmatch('[a-f0-9]{64}',expected) or hashlib.sha256(content).hexdigest()!=expected):raise ValueError('Evidence checksum differs')
    return json.loads(content)


def attestation(root,gate,name,version):
    record=read(root,gate.get('evidence'),gate.get('evidence_sha256'))
    if not gate.get('evidence_sha256'):raise ValueError('Missing evidence checksum')
    if type(record.get('schema')) is not int or record['schema']!=1 or record.get('gate')!=name or record.get('release_version')!=version or record.get('status')!='passed':raise ValueError('Stale or wrong acceptance record')
    if record.get('runtime_sha256')!=runtime_digest(root):raise ValueError('Evidence belongs to different runtime source')
    if not isinstance(record.get('reviewed_by'),str) or not record['reviewed_by'].strip():raise ValueError('Missing acceptance reviewer')
    tested=datetime.fromisoformat(record['tested_at'].replace('Z','+00:00'))
    if tested.tzinfo is None or tested>datetime.now(timezone.utc):raise ValueError('Invalid acceptance time')
    checks=record.get('checks')
    if not isinstance(checks,list) or not checks or any(not isinstance(c,dict) or not c.get('name') or c.get('status')!='passed' for c in checks):raise ValueError('Incomplete acceptance checks')
    required_scope='physical_devices' if name in PHYSICAL_DEVICE_GATES else 'security_review' if name=='security_review_and_customer_authorization' else 'operational_review' if name=='manual_update_policy_enforcement' else 'physical_installation'
    if record.get('scope')!=required_scope:raise ValueError('Evidence scope does not certify this gate')
    return record


def audit(root,release):
    root=Path(root);missing=[];gates=release.get('required_acceptance',{})
    if not isinstance(gates,dict):return ['Invalid acceptance requirements']
    for name in sorted(REQUIRED_GATES-set(gates)):missing.append(name+': gate removed')
    for name,gate in gates.items():
        try:
            if not isinstance(gate,dict) or gate.get('status')!='passed':raise ValueError('Pending acceptance')
            attestation(root,gate,name,release['version'])
        except (ValueError,KeyError,TypeError,OSError,UnicodeError,AttributeError):missing.append(name+': current reviewed evidence required')
    for name in ['engine-results.json','browser-results.json']:
        try:
            if read(root,'evidence/'+name).get('status')!='passed':raise ValueError('Failed product checks')
        except (ValueError,TypeError,OSError,AttributeError):missing.append(name)
    cores=release.get('certified_core_versions')
    if not isinstance(cores,list) or not cores or any(not isinstance(c,str) or not re.fullmatch(r'\d{4}\.\d{1,2}\.\d+',c) for c in cores):missing.append('No explicit Core versions certified')
    try:
        catalogue=read(root,'catalogue/devices.json');devices=catalogue.get('approved_devices')
        if not isinstance(devices,list) or not devices:raise ValueError('Empty catalogue')
        for device in devices:
            if not isinstance(device,dict) or any(not device.get(k) for k in catalogue.get('approval_requires',[])):raise ValueError('Incomplete device acceptance')
            if any(device.get(k) is not True for k in ['power_loss_test','offline_recovery_test','device_replacement_test']):raise ValueError('Physical checks missing')
            attestation(root,device,'approved_hardware_matrix',release['version'])
    except (ValueError,KeyError,TypeError,OSError,AttributeError):missing.append('Approved physical hardware evidence required')
    return missing
