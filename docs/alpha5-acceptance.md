# 0.4.0-alpha.5: reliability and controlled upgrades

This iteration remains an evaluation release. It does not complete every
commercial gate and is not approved for paying-customer installations.

Implemented:

- Reviewed replacement of Studio references, explicit scope acknowledgement,
  revision/capability binding, persisted duplicate receipts and paused affected rules.
- Exact-version Core compatibility guard for product mutations and runtime
  execution, with readable status and a customer-facing explanation on unknown Core.
- Non-destructive schema 1 normalization and validated saves, rejecting unknown
  newer schemas and malformed documents without resetting the home.
- Missing-device placeholders and retention during unrelated layout edits;
  new nonexistent selections are still rejected.
- Production evidence checks bound to the release and current runtime source,
  required gate set, named reviewer, test date, scope and content checksum.
- Consistent release/version and installer/runtime compatibility metadata checks.

Verified:

- 188 isolated Python tests pass, including new replacement, storage, compatibility
  and production-promotion regression cases.
- Client, connection, onboarding, home UI, recovery, household, pairing and new
  replacement browser tests pass. Mobile replacement review was visually inspected.
- Real Core 2026.10.4 fixture: member denial, inert review, replacement of room,
  schedule and visual-rule references, pausing previously enabled rules, duplicate
  approval with no second edit, unchanged simulated device states, and cleanup to
  its original layout/read-only setting. Actual schema 1 storage was checked.
- Real HAOS 18.4 lab: updated service, preserved synthetic shared home, identity
  and paused automations; actual member endpoint denials; live phone browser checks.
- Supervisor 2026.10.4 blocked catalogue reload because it was outdated. Its cold
  checkpoint and independent encrypted backup hashes were verified, one official
  manual update to 2026.10.5 was reconciled after timeout without replay, and
  health plus automatic-update=false were verified before resuming installation.
- Android code 11 is signed with the existing customer identity; signature,
  alignment and eight canonical frontend assets were verified.

Evidence is under `evidence/hardening-alpha5/`, `evidence/engine-results.json`,
`evidence/replacement-browser.json`, `evidence/android-alpha5.json` and
`evidence/source-kit.json`. GitHub CI separately checks three exact Core contracts.

Outstanding: physical radios/devices and replacement, native Android/TV camera
and notification delivery, factory/preloaded HAOS and replacement-gateway restore,
lost-owner/MFA recovery and invitations, complete all-layer manual-update handling,
public installer distribution, immutable release images, security/privacy/licensing
review and support/key-custody operations. These remain blocked production gates.
The personal HAOS installation and its configuration were not changed.

See [reliability and upgrades](reliability-and-upgrades.md) for behavior and limits.
