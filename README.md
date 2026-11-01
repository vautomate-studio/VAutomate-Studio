# VAutomate Studio

A VAutomate frontend and scoped service for one independent Home Assistant server per home, with a separate Android customer app and commissioning installer.

**Development version 0.4.0-alpha.8. Not certified for paying-customer deployment.** Production installation remains blocked by acceptance checks. The personal VAutomate application and existing household configuration are separate.

## Product

- Curated shared rooms, compact device controls and separate sensor readings.
- Lights, curtains, security, media, fans and climate through supported entity capabilities.
- Reviewed room suggestions, explicit dashboard publication and administrator-only commissioning.
- Approval-based automation templates and a visual editor; new routines default to paused.
- History, camera snapshots, room holds and bounded activity. Certified live camera streaming is pending.
- Backend role and entity-permission checks, expiring commands and no replay after connection loss.
- Remembered Android sign-in through a native encrypted vault; browser credentials stay in memory.
- Branded first-owner creation on preloaded homes, deliberate setup acknowledgement and server-side session revocation.
- Manual HAOS installer, existing-code preservation, configuration checks and exact running-version confirmation.
- Local installation inventory for many independent homes; no remote support or cloud control enabled by default.
- Administrator-only encrypted backups, independent streaming downloads, archive import and reviewed restoration. [Recovery workflow and test scope](docs/recovery.md).
- Reviewed household administration, view-only roles and password/session care with owner protection. [Account workflow and test scope](docs/household-access.md).

## Repository

| Path | Purpose |
| --- | --- |
| `frontend/` | Canonical branded customer interface and offline showroom |
| `custom_components/vautomate_studio/` | Versioned Home Assistant service and policy |
| `android/` | Separate `co.vautomate.customer` Android source; no signing keys |
| `installer/` | Bundled manual HAOS commissioning app |
| `tools/fleet_register.py` | Local inventory; no credentials or remote rollout |
| `tests/` | Isolated policy, installer and onboarding tests |
| `evidence/` | Scoped historical test reports, not blanket certification |
| `release.json` | Production acceptance requirements |

## Develop and verify

```text
python tools/verify_repository.py
python tools/test_engine.py
npm ci
npx playwright install chromium
npm test
npm run test:blueprints
python tools/build_installer.py
python tools/verify_repository.py
```

The kit is written to `dist/`. GitHub Actions test this source but cannot deploy to customer homes. Native contract checks use explicit Core versions. Production promotion is an explicit separate check:

```text
python tools/check_release.py
```

It intentionally fails until required acceptance evidence and approved hardware exist. Do not disable those checks to make a development build look released.

## Commissioning

Use a separate lab first. An installer prepares HAOS and its owner account and keeps an independent backup. Install the packaged commissioning app, explicitly allow isolated-candidate evaluation, then start it manually. It installs only its own service, preserves existing configuration and starts new installations read-only. See [installer instructions](installer/README.md).

Sign in at `/vautomate-studio/index.html`, select **Set up this home**, name the home, review suggested rooms/devices, select Home buttons and publish. Household accounts see the same saved layout, filtered by their existing read permissions. Home Care provides administrator-only commissioning status and a private local export.

A public one-click customer installation link is not live. This private source repository is not a substitute for the public distribution channel. See [repository handover](docs/repository-handover.md).

## What remains before customer release

Fresh Core first-owner creation, missing-entry installation and a real encrypted-backup restore on the synthetic HAOS lab passed. A completely fresh HAOS factory-image installation and replacement-gateway disaster recovery remain unverified. Invitations/account recovery, physical pairing and replacement acceptance, approved physical hardware, live cameras, this app identity's notifications, complete manual-update enforcement, restricted customer authorization, security/licensing review and signed immutable release distribution remain unfinished or unverified.

Earlier Core 2026.9.4/2026.10.2 synthetic compatibility results and the dev.3 full HAOS lab results are historical evidence with their own scopes. They do not certify all Core versions, physical devices or this new source version. Read the [commercial status](installer/COMMERCIAL-STATUS.md) and [acceptance plan](docs/acceptance.md).

Original VAutomate material is not offered under an open-source license. Keep the repository private until the owner deliberately chooses a distribution policy. Read [security guidance](SECURITY.md), [notices](NOTICE.md) and [contribution requirements](CONTRIBUTING.md).
