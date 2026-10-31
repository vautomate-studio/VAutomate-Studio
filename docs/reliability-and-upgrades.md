# Reliability and controlled upgrades

VAutomate remains an evaluated candidate. No software can promise compatibility
with every future Home Assistant version, Android version, vendor service or device.
Manual updates give the administrator control over timing; they do not remove
the need for a supported maintenance and recovery process.

## Runtime compatibility

The service names exact Core versions whose contracts are checked in CI.
An untested Core starts Studio with device execution disabled. A deliberately
small read-only product API remains available; unknown/new operations do not
inherit write access. Layout changes, pairing, account changes, replacement,
backup creation/restoration/import and rule edits are rejected until a compatible
VAutomate release is installed. The frontend explains this state.

This protects Studio operations; it does not disable external Home Assistant
automations or third-party integrations. Older code cannot acquire this guard
retroactively, so use the tested installer and recovery process when upgrading.

The installer and runtime version lists must match. Package, service, Android and
installer versions are checked together. Source kits use canonical LF text and
a reviewed cross-platform checksum. Android versions are read from the manifest
by the build tool, and signing uses the established customer app identity.

## Stored home data

Legacy documents are validated and copied into schema 1 without erasing unknown
metadata, installation identity or selections for missing devices. Migration is
persisted on the next successful save. Writes are validated before the existing
Home Assistant Store commits them; in-memory state changes only after persistence
succeeds. A newer unknown schema or a malformed/bounded-out document is rejected
without resetting the saved home. Restore a known good full backup or use a
compatible service version; do not edit a schema number to force a downgrade.

An existing missing device stays visible as unavailable with no operations.
It does not prevent unrelated room edits. New nonexistent entities still cannot
be added. Original device identifiers are retained until an explicit removal or
reviewed replacement, so recovery does not silently discard household choices.

## Reviewed replacement

Home Care → Replace a device migrates Studio rooms, Home buttons, schedules and
semantic entity fields in visual automations. Pair and discover the new control
first without assigning it elsewhere. Choose a replacement of the same domain,
reading class and unit; existing actions must still validate. Missing-original
details are explicitly disclosed. Review affected references and acknowledge
that native HA scenes and external automations need separate review.

The review expires, belongs to the reviewing administrator, and is bound to the
home revision and device capabilities. Commit rechecks administrator access and
the review, saves once, and pauses affected rules. It dispatches no device action,
changes no radio or HA registry entry, and leaves unrelated rules untouched.
Duplicate approvals return a persisted receipt. Test the replacement and review
each affected rule before deliberately enabling it again.

## Release evidence

`tools/check_release.py` requires every named acceptance gate, explicit certified
Core versions and an approved physical hardware catalogue. A gate attestation
must be JSON with schema 1, its exact gate name and `release_version`, `status:
passed`, `reviewed_by`, a timezone-aware `tested_at`, passing named `checks`, the
appropriate physical/security/operational `scope`, and `runtime_sha256` from
`tools/release_policy.py`. Its path and SHA-256 belong in that gate's `evidence`
and `evidence_sha256`. The runtime digest covers service, native Android source
and installer code; old evidence cannot silently certify changed code.

These attestations are reviewed records, not signatures or a substitute for
independent security and hardware testing. Current reports remain partial
evaluation evidence. Production promotion is blocked until the missing real
acceptance and human release review are complete.

## Supervisor support

The lab demonstrated that an old Supervisor can block catalogue refreshes even
with manual-update policy configured. Its verified cold checkpoint and independent
encrypted backup were retained, then one explicit official update was reconciled
after a timeout. Automatic updates stayed disabled. Do not bypass job conditions
or network-block the platform to simulate a supported frozen installation.

Home Assistant documents that [only the latest Supervisor is supported](https://www.home-assistant.io/more-info/unsupported/supervisor_version/).
The [official update endpoint](https://contributors.home-assistant.io/apps/supervisor-api/supervisor/#post-supervisorupdate)
installs the latest version; arbitrary version pinning is not supported in a normal
Supervisor installation. Customer support plans must account for this limitation.
