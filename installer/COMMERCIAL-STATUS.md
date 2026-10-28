# Commercial commissioning status

28 October 2026. Source version 0.3.0-dev.4. The historical live HAOS installation and Android artifact results below belong to 0.3.0-dev.3; the repository source has additional CI, distribution and encoding improvements.

## Delivered and checked

- Manual HAOS app installer, verified bundled files, configuration validation, existing-component preservation and an exact running-version health check.
- A real local-app build/install on HAOS 18.4 / Core and Supervisor 2026.10.4. Studio reports ready for onboarding; a repeated installation does not request another Core restart or create another service entry.
- Existing shared lab room, installation identity, evaluation controls and paused automation selections remain intact. Personal HAOS is unchanged.
- Guided shared-home setup, inert suggestions from current room/device assignments, explicit publish, admin-only commissioning status and a private local record export.
- Local SQLite inventory for many independent installations. Imports are validated, deduplicated and rejected if older than an existing record. No customer credentials, addresses or remote control are collected.
- 80 isolated automated regression tests; responsive showroom onboarding checks; live admin/member API checks and desktop/mobile status/export checks.
- Separate signed Android development APK with verified bundled frontend source. Signature and alignment checks pass. It has not been tested on physical Android hardware in this run.

## Not a customer release

The public GitHub repository and installation link are not live. The owner must finish GitHub account verification and supply the username. No account, mail access, hosting or public publication has been created implicitly.

Clean-server first-owner setup, invitations/account recovery, guided device pairing/replacement, approved physical hardware, live-camera acceptance, this app identity's phone-notification delivery, backup/restore drills, full manual-update enforcement across all platform/firmware/phone layers, security review and signed immutable container release distribution remain incomplete. The production release gate intentionally refuses promotion. The installer requires an explicit isolated-candidate override.

HAOS's first owner account and initial server preparation remain installer tasks. Customers should receive a commissioned home; do not hand over this development kit as a finished product. The local fleet register is an inventory tool, not a remote fleet-management service.

The previous private VM checkpoint predates these changes. It is not a tested full Home Assistant disaster-restore result. Store full independent backups and verify restoration on spare hardware before any customer rollout.
