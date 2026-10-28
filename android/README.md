# VAutomate Studio — commercial customer candidate

Version **0.3.0-dev.4**, API **v1**. This working build includes the manual HAOS commissioning installer, reviewed room suggestions, private installation records and connection hardening. Release status: **evaluation candidate; not certified for customer deployment**.

Latest hosted customer APK remains RC4. A separate local 0.3.0-dev.4 evaluation APK and commissioning kit are available; neither is a production release. This source additionally contains a manual-update commissioning policy, seven native occupancy/home-mode blueprint drafts and a shared-home notice in custom authoring. None of these changes has been installed on the personal server. Native blueprint creation from VAutomate and enforcement of every update setting remain pending. See `docs/commercial-priorities.md` and `docs/connection-stability.md`.

This is a separate product source tree. It does not replace the personal VAutomate app or the immutable Studio Preview. No installation or configuration change has been made to the existing home server. A separate, network-disabled showroom is available for evaluating the interface with simulated devices.

## Implemented

- Purposeful Home, Rooms, Routines and Home Care navigation; no Home Assistant backend links or embedded administration workspace.
- Official short/long logos, complete arrival animation, collapsible navigation, mobile overlay navigation, three finishes, reduced-motion handling and remote/keyboard navigation.
- Room master lights/fans/switches: any member On means On; tapping turns all selected members Off. All-Off turns all On. Members are preflighted before dispatch. Offline members produce a clear error rather than an incomplete success.
- Capability-based controls for lights, curtains, media, fans, climate, scenes and home-mode helpers. Information sensors have a separate presentation. Active presence/door indicators are shown only when relevant.
- Guided shared Studio layout setup: home name, welcome line, curated room/device selections and up to four scene/helper buttons. Layout commits use revision checks and atomic backend storage. Existing HA dashboards, areas, device names and automations are not rewritten by this editor.
- Backend-validated editable time/day routines, pause/resume and removal. The backend schedules them even when the phone is closed. Run reservations are persisted before dispatch; missed schedules are not replayed. Unattended alarm commands are excluded.
- Bounded 24-hour history API with touch/keyboard graph inspection. Recorder must be configured and retain the selected entity.
- Authenticated camera snapshots with full-screen viewing. This candidate does not claim tested live-video playback.
- Server-side administrator checks, HA read/control permission checks, explicit managed entities, action/parameter allowlists, short command expiry, duplicate-request protection and bounded rate limits.
- Alarm code entry is transient, never saved in layouts, activity or the request cache. Raw backend exceptions and entity attributes containing camera credentials, GPS, tokens or integration secrets are withheld.
- Android shell with an independent identity, encrypted remembered sign-in, normal HA authentication/MFA flow, local/remote connection profiles and no generic backend browser navigation.
- Unit/transport/browser tests, screenshots, pinned browser-test dependencies, CI compatibility smoke tests and a production promotion gate.

## Approval-based bundled routines

The library now includes Morning light, Evening comfort, Goodnight and Evening breeze. Browsing/reviewing does not create or run anything. Only explicit administrator approval creates an independent editable copy, paused by default; enabling is a separate deliberate choice. Reviewed plans expire, are bound to their approver and current home revision, and are revalidated before saving. Retrying a submitted approval cannot duplicate the routine. Existing instances are never silently changed by a later library release.

These four bundles use time/day schedules. RC3 adds seven entity-bound room/home templates and an optional complex visual editor with state/numeric/time/sun triggers, grouped conditions, branches, waits, repeats and parallel actions. Preview and explicit administrator approval are required; rules default to paused. The runtime uses native HA Script blocks with a private dispatch gate, fresh permissions and per-room holds. Simulated tests pass; native HAOS/hardware certification remains a production gate. See `docs/automations-and-maintenance.md` for the accepted scope and proposed maintenance policy. No live update settings were changed.

## Android identity

Customer development build: **VAutomate Studio Home**, package `co.vautomate.customer`, version `0.3.0-dev.4`.

Personal VAutomate remains `co.vautomate.home`. Studio Preview remains `co.vautomate.studio`. They have independent Android storage, providers, vault aliases and signing certificates. Installing the customer candidate does not upgrade either older app.

The customer app always uses its bundled frontend. It expects the versioned Studio service on the entered server. A server without that service shows installer setup guidance; it does not silently fall back to the personal dashboard or original HA frontend. Browser sessions keep credentials in memory. Android sessions can be remembered in the native encrypted vault. No password is saved.

## Manual commissioning installer

See [installer/README.md](installer/README.md) for the packaged installer, existing-room suggestions and local multi-home inventory. A real HAOS lab install and repeat install passed, including exact runtime version confirmation and preservation. The public repository/link, clean-server first-owner flow and physical customer acceptance remain unfinished.

## Install on an isolated commissioning server only

1. Prepare a separate HAOS installation. Establish its owner/account access and an independently stored backup. Do not install this candidate on the current personal home as part of read-only testing.
2. Copy `custom_components/vautomate_studio` into that server's `config/custom_components` directory, retaining its existing contents. Restart Core during an agreed maintenance window.
3. An installer adds the **VAutomate Studio** integration once. It starts read-only. This initial installer installation currently uses HA integration setup; customer handover must not require the customer to perform it.
4. Open `/vautomate-studio/index.html` or install the dedicated Android customer APK and enter that test server's address(es). Sign in with a home account.
5. Use Personalize to curate rooms and controls, preview, then publish the Studio layout. All accounts using the service read the same layout, filtered by their existing HA read permissions.
6. On the isolated server only, the integration's options can explicitly enable **Allow device commands during evaluation**. This is a laboratory override, not a certification or recommendation for customer homes.
7. Run the physical device, permission, outage, update and restore acceptance plan before considering any production promotion.

The integration persists only its own `vautomate_studio.commercial.v1` storage document. It never directly edits existing HA `.storage` documents. Corrupt or unsupported storage is kept and setup fails for recovery; it is not silently reset. Disabling or removing the integration disables its API and scheduler. Static assets may remain registered until Core restarts; they contain no credentials.

## Release limitations

**Not implemented/approved for customer release:** guided Zigbee/Matter pairing and replacement, first-owner creation and invitation/account-recovery flows, managed Supervisor/OS/Core update execution, off-device backup orchestration and restore, persistent phone notification delivery for this new app identity, certified camera live video, an approved hardware catalogue, restricted-room guest delegation, and a fleet/support management service.

These functions are not represented as working controls. Feature flags report them unavailable, Home Care reports pending validation, and `release.json` has no certified Core versions. The generic HA platform does not supply a promise that arbitrary third-party integrations will behave the same way.

Role checks protect Studio operations and respect HA permissions. Hiding backend navigation is not network isolation. An account's existing HA token can still use other HA APIs permitted to that account. Restricted-room guests or a strict customer-only gateway require separate backend/network authorization work and security review; this candidate does not claim to implement that boundary.

The compatibility adapter has a **Core 2026.10.2** source/API baseline. A separate WSL Core-container lab now passes real native Script, Studio API and browser tests using synthetic devices. These tests are distinct from full HAOS/Supervisor, physical-device and Android certification, which remain pending. Supervisor and OS workflows are gated separately. Core updates, integration/firmware changes and Android WebView changes must be tested before rollout. Backups must be restored in a drill; installing an older Core version alone does not reverse data migrations.

## Development and evidence

Run from this directory:

```text
python tools/test_engine.py
npm ci
npx playwright install chromium
npm test
python tools/check_release.py
```

The release check intentionally exits **2** while acceptance gates remain pending. Do not remove gates or rename the candidate to "production" to bypass it. Test results and responsive screenshots are in `evidence/`. Browser tests serve only local showroom fixtures and reject external requests.

For the real Core API import/feature smoke test, use a disposable official container (no home configuration mounts):

```text
docker run --rm -v "$PWD:/src:ro" -w /src --entrypoint python ghcr.io/home-assistant/home-assistant:2026.10.2 tools/ha_contract.py
```

CI also checks the current `stable` image so upstream changes produce a visible failure instead of an automatic customer deployment. CI has been authored, not executed on a hosted repository in this session. An actual local Docker daemon/Linux test environment was unavailable; the Core container smoke test and full HAOS tests remain pending.

Android source is supplied separately. It builds with the included portable SDK build script and the existing pinned JDK/SDK/dependencies. Private signing material is excluded from every delivery archive. The signed candidate uses a separate local release-testing certificate; store distribution and production signing custody remain release work.

See `docs/acceptance.md`, `docs/api.md` and `catalogue/devices.json` before commissioning.

## RC3 automation implementation

See `docs/visual-automations.md` for the implemented contract, bounds, runtime behavior and remaining acceptance work. No personal server settings or live automations were changed. The manual-only policy is a desired commissioning requirement, not evidence that an existing server has been frozen.
