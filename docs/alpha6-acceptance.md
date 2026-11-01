# Alpha.6 acceptance scope

This is a development candidate, not production certification.

- Manage home supplies room creation/edit/removal, physical-device grouping, registered control naming, room assignment and shared dashboard cards. Cards can be added, resized, moved and removed.
- Zigbee & connections has an explicit approval flow for ZHA, Zigbee2MQTT/MQTT and seven curated LAN integrations. Its UI renders supported native forms and stops on unsupported steps. Native credentials remain transient; no generic configuration-flow or Supervisor proxy is exposed.
- Actual HAOS 18.4 / Core 2026.10.4 / Supervisor 2026.10.5 lab installation preserves its shared room and paused automations. Non-admin users are denied integration setup, registry rename and installer controls at the backend.
- The real initial ZHA coordinator form serializes and cancels successfully. No radio is attached: pairing, coordinator migration, actual Zigbee2MQTT radio operation and physical-device behavior are not certified.
- Personal and Studio share the ten interaction states in [the state standard](ui-state-standard.md): empty, loading, error, offline, slow network, no results, permission, expiry, validation and success. Safe restoration never actuates controls; uncertain writes never retry automatically.
- Isolated browser tests and 215 Python tests pass locally. Android signature/alignment and all eight bundled Studio assets are verified. Physical Android/TV interaction remains a separate acceptance task.
- Personal frontend work is confined to versioned frontend assets and its index references. Home Assistant configuration and Home Control dashboards are unchanged. Windows and TV load the hosted Personal interface; Android needs the updated package for its bundled UI.

Evidence is under `evidence/alpha6`, `evidence/ui-states-browser.json` and `evidence/management-browser.json`. CI must independently validate the exact commit. Existing commercial hardware, security, recovery, distribution and support gates remain open in `release.json`.
