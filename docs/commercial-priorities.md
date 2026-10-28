# Commercial product priorities

Owner requirements from 2026-10-28. These requirements do not certify current runtime behavior or authorize changing the personal server.

## 1. Manual-only updates

The chosen product policy is **manual installation only**, including VAutomate, Core, OS, Supervisor, apps/add-ons, approved integrations and managed firmware where the platform supports control. No silent rollout, automatic package download or automatic installer is permitted. Update metadata checking is manual by default. An urgent fix may be recommended to an administrator; it is not installed without that administrator's action.

`policy/updates.json` is the desired policy, not evidence of applied settings. Commissioning must inspect every applicable layer, disable supported automatic installers and update automations, verify the resulting state and disclose any layer that cannot be controlled. Store/app auto-update settings on the customer's phone and vendor cloud changes are outside this service's authority. Do not claim a completely frozen environment without evidence.

Supervisor can be configured for manual updates, but only its latest version is supported upstream. An older version must be identified as outside upstream support. Keep normal watchdog/recovery behavior separate from installers. Do not block network traffic, tamper with permissions or bypass Supervisor checks to simulate update control. No update flags on the personal server were changed.

Primary source: https://www.home-assistant.io/more-info/unsupported/supervisor_version/ and https://contributors.home-assistant.io/apps/supervisor-api/supervisor/ .

## 2. Entity-bound automation library

In addition to the four implemented time/day bundles, native-HA blueprint drafts now cover room entrance/exit, vacant-room lights off, bathroom occupancy lighting, hallway motion, bathroom humidity ventilation, sunset curtains and helper-driven Dawat/Cinema/home modes. See `automation_packs/occupancy-v1/README.md` for exact current status.

Only entities should be required for ordinary setup; documented timing/threshold defaults are supplied. Optional settings remain editable. Suggestions are inert until explicitly approved. Create each customer-owned instance paused unless enabling was deliberately selected. Preview affected devices, trigger/delay, pause conditions and the expected effect on other occupants. Keep source versions and do not overwrite existing instances when a library changes.

Presence and motion are not interchangeable. Bathroom rules require tested coverage for stationary occupants and shower/toilet positions. A door close is not proof of vacancy. Unknown/unavailable readings must not cause switch-off. Support absence confirmation, manual hold, per-room pause and optional Sleep/Cinema/Dawat guards. Warn about overlapping rules before creation; never silently disable another rule.

RC3 implements equivalent recipes through the versioned Studio rule API and native Script adapter, with visual entity binding and approval. The separate YAML blueprint pack remains a structural draft, not the runtime deployment format. Native Core/HAOS validation and physical acceptance remain pending; neither implementation is certified for customer installation.

## 3. Optional custom automation with shared-home care

Advanced authoring remains the administrator's choice. It must use visual triggers, conditions, branching, waits/repeats and actions; no mandatory YAML workflow. RC3 implements the visual editor and bounded execution contract; native and physical acceptance remain pending.

The current development schedule editor now shows this notice before saving a custom change:

> What feels right to you may disturb someone else. Discuss changes, respect privacy, keep manual controls available, and test before enabling.

It asks the author to acknowledge the effect on other people. The acknowledgement is a UX reminder, not a legal waiver, permission bypass or substitute for validation. Apply the same pattern to the future complex editor, along with conflict checks, simulation, clear traces and deliberate physical testing.

## 4. Priorities before expanding the feature list

1. **Installer commissioning and customer handover:** approved hardware, room naming, range/sensor coverage, curtain direction/limits, camera quality, test checklist, invitations and account recovery. Customers receive their finished home without technical setup.
2. **Shared-home behavior:** per-room pause/manual hold, guest/DND/Sleep modes, predictable mode priorities, conflict warnings, understandable activity and undo/restore where safe.
3. **Device replacement:** identify a failed device, pair its replacement and review the room/scene/automation references to migrate. No silent changes to unrelated configuration.
4. **Recovery and local resilience:** independently stored backups, tested restore to spare hardware, storage/radio health, graceful loss of internet/server/device and verified physical controls.
5. **Access and privacy:** backend roles, approved temporary installer access, visible consent for cameras/location/remote diagnostics, credential revocation, redacted diagnostics and clear data ownership. Menu hiding alone is insufficient.
6. **Support operations:** installation record, hardware/firmware inventory, approved version matrix, customer-visible service history, reproducible support package and release signing/key custody.
7. **Customer usability:** consistent controls on phones/tablets/TV, accessibility/large text, suitable language support, helpful alerts, simple names and no technical identifiers on normal screens.

Keep basic installed local control usable without a care-plan renewal or programmed commercial expiry. State the supported maintenance period clearly and fund it sustainably. Neither manual updates nor a subscription-free design is a promise that hardware, external services and old phone software will work forever.
