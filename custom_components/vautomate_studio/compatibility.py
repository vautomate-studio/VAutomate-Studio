"""Explicit runtime contracts. An untested Core is readable, never writable by default."""
from __future__ import annotations

CONTRACT_CHECKED_CORES=frozenset({'2026.9.4','2026.10.2','2026.10.4'})
# A short explicit read surface prevents a new mutation from accidentally bypassing
# the compatibility gate. No version ranges imply tests that have not been run.
READ_OPERATIONS=frozenset({'bootstrap','snapshot','discover','commissioning/status','care','activity','history','camera/snapshot','accounts/me','accounts/list','pairing/status','backups/status','bundles/list','automations/library','automations/traces','replacements/status','compatibility/status'})


def status(version):
    checked=version in CONTRACT_CHECKED_CORES
    return {'core_version':version,'contract_checked':checked,'certified':False,
            'status':'evaluation' if checked else 'unsupported_core',
            'writes_allowed':checked,'checked_core_versions':sorted(CONTRACT_CHECKED_CORES),
            'message':'Physical hardware and commercial acceptance are still required.' if checked else 'This Core version has not been tested with this VAutomate release. Home readings remain available; changes are paused until a compatible VAutomate release is installed.'}


def guard(version,operation):
    if version not in CONTRACT_CHECKED_CORES and operation not in READ_OPERATIONS:
        from .engine import ProductError
        raise ProductError('unsupported_core','Changes are paused because this Core version is untested. Install a compatible VAutomate release before changing this home.')
