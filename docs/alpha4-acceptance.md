# 0.4.0-alpha.4: reviewed device onboarding

The candidate adds administrator-only ZHA/Zigbee2MQTT pairing and explicit shared
room placement. It retains read-only evaluation defaults, manual updates and
`production_ready: false`. Hardware models have not yet been selected.

Verified in this iteration:

- 159 isolated policy/adapter tests pass, including pairing approval ownership,
  expiry, unknown results, no replay, restart interruption, journal failure,
  revision conflicts, MQTT transaction matching, inventory limits and redaction.
- The complete client and browser regression suite passes. The new inert pairing
  browser fixture checks deliberate approval, readiness, stable focus during
  polling, room placement, explicit closure, mobile fit and member isolation.
- A real local-app update on the isolated HAOS 18.4 / Core 2026.10.4 lab preserves
  its synthetic room, installation identity and paused automations. Real member
  requests to every pairing endpoint are denied. No-radio status is graceful.
- Android code 10 is built, signed with the established customer identity,
  signature/alignment verified, and its eight canonical frontend assets match.
  The build tool now reads the version directly from the Android manifest.
- The commissioning source archive is checked against its recorded SHA-256;
  independent Linux CI must reproduce it.

Evidence: `evidence/engine-results.json`, `evidence/pairing-browser.json`,
`evidence/pairing-alpha4/haos-install.json`, `evidence/android-alpha4.json`,
`evidence/source-kit.json`. Existing recovery/account evidence remains scoped
to its recorded versions; it is not relabelled as a new physical acceptance run.

This is not physical Zigbee, camera, Android/TV, replacement-gateway restore,
or production acceptance. Device replacement, radio provisioning, notification
enrolment, lost-owner recovery and public one-click distribution remain open.
The personal home configuration is unchanged. See [device onboarding](device-onboarding.md)
for protocol scope and limits.
