# First-home onboarding — 0.4.0-alpha.1

29 October 2026. Development evidence, not customer certification.

## Customer journey

An installer prepares an independent HAOS gateway and preloads the versioned Studio component plus its welcome assets under `/config/www/vautomate-setup`. On an empty Core configuration, the welcome page at `/local/vautomate-setup/index.html` is available before an owner exists. The customer explicitly confirms a new-home setup, chooses a name, username and password, then VAutomate creates the owner and finishes the required platform setup. Analytics are not opted in. The scoped Studio service is activated and its authenticated health is checked before showing the dashboard. The administrator then reviews rooms/devices and publishes the shared home.

No token, YAML or Home Assistant frontend is needed for this tested customer path. The server package must already be present: the Android app cannot install arbitrary server code on a bare HAOS machine. This alpha has no public one-click installer or factory image yet.

Existing homes use the normal sign-in path. First-owner creation cannot overwrite an existing owner. If the owner was created but later setup failed, Continue resumes the signed-in setup instead of creating another account. Unknown setup steps and missing packages stop with an actionable error. Password fields are cleared after submission. Android can remember sign-in in its encrypted native vault; the browser holds credentials in memory. Sign-out revokes the refresh token at the server's token endpoint.

## Verified boundaries

- A disposable fresh Core 2026.10.4 configuration ran on the existing HAOS test server. Before setup, all four onboarding steps were incomplete and the VAutomate welcome page was available. Actual account creation, platform setup, service activation, shared-room publication and a separate real member login passed.
- The member received the published layout and was denied discovery, installation identity and publication. Signing out invalidated the actual refresh token.
- Separately, the main HAOS 18.4 lab's own Studio entry/store was preserved and removed. The real commissioning app installed the alpha and created exactly one loaded entry, an empty home and read-only defaults. The synthetic dashboard and paused rules were restored and checked afterward. Repeat install did not request another restart.
- Desktop and phone browser checks passed against the restored HAOS lab. The 390px phone view had no horizontal overflow or uncaught page errors.
- Automated checks cover both legacy hexadecimal and current ULID setup identities, active/stale locks, interrupted rename recovery, revision/permission checks and safe sign-out.

Reports: [fresh owner](../evidence/first-home-alpha1/first-owner-live-result.json), [clean Studio install](../evidence/first-home-alpha1/clean-studio-install-result.json), [HAOS permissions](../evidence/first-home-alpha1/commissioning-result.json), [live browser](../evidence/first-home-alpha1/browser-commissioning-result.json).

These tests did not provision a fresh HAOS/Supervisor image, attach physical radios/cameras, restore a full backup or run the new APK on a phone. The personal home was unchanged. All production acceptance gates retain their actual pending scope.
