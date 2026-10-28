# Automation ownership and maintenance policy

Product requirements accepted from the owner. Maintenance recommendations below are a proposal, not a customer contract or an instruction to change the existing home's update settings.

## Bundled routines: available, never imposed

The library is preloaded as versioned, inert definitions. Browsing, onboarding and previewing must never create or enable an instance or operate a device.

Implemented in this candidate: Morning light, Evening comfort, Goodnight and Evening breeze. These are **time/day schedules**, with explicit device selection. They are not presented as motion-, presence- or sunset-triggered automations.

Flow: choose a bundle → choose devices/time/days → review the exact actions → approve creation. Creation defaults to **paused**. An administrator may deliberately choose **Enable after creating**, changing the confirmation to **Approve & enable**. The service must be in control-enabled evaluation mode to accept that choice.

Review produces a short-lived, account-bound approval nonce. The server retains the reviewed plan and revision; approval cannot substitute a different plan. It rechecks identity, device permissions and capabilities. A failed disk commit preserves the previous document and can be retried. A repeated approval returns its receipt without creating another instance. No security code or raw approval nonce is persisted in the routine.

Every approved instance is a materialized, independent copy recording its source ID/version and approver in backend storage. Customer edits are retained and marked customized. Library updates must not silently rewrite existing instances. A future library upgrade must show a change preview and request another explicit decision. No template remotely supplied by an untrusted URL is executed automatically.

Administrators create/edit/publish automations. Other accounts get only the actions and state allowed by their backend permissions. Customer choice does not mean that a guest may grant itself administrative permissions.

## Optional complex visual automations

This remains required development work before production approval. The current schedule editor is not a complete complex automation editor.

The customer must be able to choose **Create automation** and use a visual editor for triggers, conditions and actions without being required to write YAML. Everyday users need not open that editor to use the home or the bundled library. Advanced features appear when the user chooses them.

Required editor/runtime scope:

- Multiple triggers: time, sun, device/entity change, presence and supported events; clear names and trigger IDs.
- Conditions: AND/OR/NOT groups, state/numeric/time tests and editable nested branches.
- Actions: explicit targets, device actions, modes/scenes, choose/if branches, delay, wait with timeout, bounded repeat and parallel branches.
- Execution mode selection, readable summaries and warnings about overlapping/conflicting actions.
- Draft, validate, review, approve/create, optional enable, pause, duplicate, edit and delete.
- A simulation/trace view distinct from running real device actions; testing on physical devices requires an explicit user action.
- Permission validation, bounded resources, cancellation, understandable partial-failure states and no command replay on reconnect.
- Native HA automation semantics or an equally validated adapter, isolated through the versioned product API. Do not implement a misleading subset and call it full HA automation compatibility.

Custom automations belong to the customer. Product/library updates must preserve them. Advanced authoring is optional, but available for supported features once implemented and validated. Unattended security-sensitive operations require a separate design and review; no bundled routine silently disarms the home.

## Chosen update policy and proposed care model

- The owner selected manual-only updates on 2026-10-28. Nothing is to be installed automatically; critical fixes can be recommended but still need deliberate manual installation. See `policy/updates.json` and `docs/commercial-priorities.md`.
- Review upstream security notices and compatibility continuously/regularly; do not leave a known critical issue until the next annual appointment.
- Use tested maintenance windows for Core, OS, integrations and firmware; take an off-device backup and verify recovery before risky upgrades.
- Supervisor is a distinct layer: its automatic-update setting must be disabled and verified during commercial commissioning. Only its latest version is supported upstream; running an older version carries that support limitation. This setting has not been changed on the existing personal server.
- An annual health check covers backups/recovery readiness, storage, radios, batteries, account access and physical device operation. This is separate from security patch response.
- Cost a defined included initial support period (recommendation: first year), then an optional renewable care plan. Do not promise free annual maintenance for every customer indefinitely before funding support, travel, testing, recovery and any external services actually used.
- Basic local control should not be disabled merely because a maintenance plan ends. Do not introduce a subscription kill switch or planned expiry for already-installed local controls. Optional cloud/remote services can have separate provider and service requirements.

An old local installation may continue operating for years, but "works forever without maintenance" is not a supportable product promise. Storage/hardware/battery failure, network changes, mobile platform changes, integrations and external provider APIs can require repair or updates independently of a frozen Core version. No permanent-operation guarantee has been made.

No update flags on the existing personal HAOS installation were changed to apply this proposal.

Primary references reviewed:

- https://www.home-assistant.io/docs/automation/using_blueprints/ — reusable templates and the consequences of updating inherited blueprints.
- https://www.home-assistant.io/more-info/unsupported/supervisor_version/ — latest Supervisor version support requirement.
- https://contributors.home-assistant.io/os/supervisor/architecture/ — different automatic/manual update behavior of system layers.
- https://www.home-assistant.io/common-tasks/os/ — update, backup and recovery guidance.
