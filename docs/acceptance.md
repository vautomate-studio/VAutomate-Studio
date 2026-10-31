# Commercial acceptance plan

Use a separate HAOS installation. Never exercise these writes, failures or restore drills on the personal server under its read-only testing authorization.

Record model, firmware, integration version, Core/Supervisor/OS versions, app/WebView version, date, tester, results and evidence for each accepted configuration. A UI screenshot or a mock pass cannot certify physical operation.

1. **Installation and handover:** clean supported HAOS, initial owner, installer setup, customer account, invitations/revocation, wrong-server detection, remote/local switching, password/MFA changes, recovery, no customer backend handoff. Initial owner creation is implemented and tested on a fresh Core fixture. Invitations and lost-owner recovery remain pending.
2. **Hardware:** lights (on/off, dimming/temperature where available), curtains (direction, stop, safe limits/calibration and optional position), panels/cameras, media sources/volume, fans and climate. Verify real state confirmation, power loss, radio reconnection, low battery, replacement and unavailable-device UX.
3. **Room masters:** mixed states, all Off, unavailable members, concurrent phones and permission-restricted entities. No reordering or focus loss on Android/TV.
4. **Security:** correct/wrong/missing codes, repeated attempts, delayed responses, reconnects, log redaction and no unintended disarm. Prove native HA permissions as well as Studio checks. Test direct API attempts; menu hiding is not a permission boundary.
5. **Onboarding:** Zigbee pairing windows stop automatically, cancellation/retry/replacement, Matter/Thread phone requirements, diagnostic entities excluded, friendly room assignment and no technical naming burden. ZHA/Zigbee2MQTT pairing and Studio reference replacement have software guards; physical acceptance remains pending.
6. **Shared editing:** two administrators, stale revision, disk full, restart during commit, corrupt storage, room removal and household views. Preserve previous layouts and unrelated HA configuration.
7. **Routines:** correct timezone/days, daylight-saving changes, restart in the scheduled minute, disabled/deleted routine, revoked owner, offline device and partial action failure. Persist run reservations and do not replay missed schedules.
8. **Updates:** Core previous supported version to target, service version migration, Supervisor/OS separately, integration and device firmware, interruption/failure. Pilot first; maintain security patch turnaround and support records.
9. **Recovery:** off-device encrypted backup and key custody, successful restore to spare hardware, radio/coordinator recovery, customer app reconnect and failed-update recovery. A backup-success notification is not restore evidence.
10. **Platforms:** physical Android 12 onward, S23 Ultra/Android 14, TV remote, large text/accessibility, screen readers, pause/resume, native splash, app upgrades, encrypted session persistence/revocation and full-screen cameras. Browser viewports are preliminary evidence only.
11. **Alerts:** registration for the new customer identity, bell/phone notifications, permission denial, background limits, revoked sessions, remote downtime and no duplicated alerts. This candidate has not ported the personal app's delivery implementation.
12. **Operations:** support access authorization/expiry, privacy, credential/key rotation, release signing, support ownership, catalogue maintenance, multi-home isolation and incident handling.

Do not enable unvalidated maintenance actions, mark generic devices "approved", publish a certified Core range or advertise customer deployment while the corresponding gate is pending. Complete test evidence, then conduct a human production release review.
