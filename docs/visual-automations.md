# Visual automations: RC3

Implemented in the separate Studio commercial product. This is evaluation software, not a certified customer release. No integration was installed on the personal server.

## Customer interaction

Routines offers seven entity-bound recipes: room entrance/exit, room exit only, bathroom presence lighting, hallway motion lighting, bathroom humidity ventilation, sunset curtains and home-mode scenes. Setup supplies timing defaults; the administrator selects compatible devices already curated into the relevant Studio room. Bathroom presence requires an explicit stationary-person/shower coverage confirmation. Motion is never described as proof of vacancy.

The optional visual editor supports state, numeric, time/day and sun triggers; all/any/not, state, numeric, time and trigger conditions; device actions, delay, wait, condition stops, branching, fixed repeats and parallel branches. No user YAML, Jinja or arbitrary service name is accepted. Comfort automations exclude security/lock/server-maintenance actions. The separate alarm UI remains available for direct, permission-checked operation.

Review compiles and validates against the installed Core script schema, displays an inert current-state simulation, and warns about overlapping enabled Studio automations/schedules. External HA automations are outside this conflict analysis. Custom changes require the shared-home acknowledgement. Reviews expire after five minutes and bind the account and layout revision. Approval is idempotent; all rules default to paused. Enabling requires an explicit choice and an evaluation server with commands enabled. Edits require a new review; no library update silently rewrites existing instances.

## Runtime behavior

HA native Script implements choose, repeat, parallel, delay and wait semantics. Compiler-produced blocks call a private execution gate. Each device dispatch resolves the current owner identity again, verifies administrator status and current entity permissions, validates the approved command and checks the current record, mode guards and room hold. There is no generic backend service proxy. Private execution tokens are absent from customer activity responses.

Known state/numeric crossings trigger execution. Unknown/unavailable readings cancel confirmation timers. Recovery, startup and room-hold expiry do not synthesize a fresh crossing or replay missed actions. Single mode ignores retriggers while running; restart mode cancels the prior run. Daily time/sun reservations persist before dispatch to prevent ordinary restart/repeated-local-time replay. Runs are not restored after a server restart. Manual device control remains available during a room hold. Scene actions conservatively respect every active room hold because scene members can extend beyond the displayed target.

Bounds: 100 stored rules, 120 blocks per rule, six validation nesting levels, 200 expanded device actions, four parallel branches, repeat counts up to 20, one hour total configured delay/wait budget, eight concurrent runs and no queued replay. Actual device requests expire after 15 seconds and are never automatically retried. Interrupted requests record an unknown outcome so the user checks the current device state before retrying.

Activity is an in-memory bounded diagnostic list, not a durable audit archive. Removing the integration stops its scheduler and active runs. Studio changes are stored only in its own storage document.

## Evidence and limits

`tests/test_rules.py` validates templates, bounds, compiler, simulation, account/revision approval, conflicts and room holds. `tests/test_runtime.py` exercises event timing, vacancy cancellation, holds/modes, revoked permissions, cancellation, private-step ownership, no startup replay and persisted time reservations using a simulated adapter. `tests/browser.cjs` tests template review, default-paused approval, visual authoring, acknowledgement, no command execution during preview and room pause/resume in the offline showroom. These do not prove native Core execution or physical sensor behavior.

RC4 development established a separate WSL2 Core-container lab. Native Core 2026.10.2 import/Script tests and actual Studio API/browser tests now pass with synthetic entities, including a real 30-second vacancy confirmation, room holds, member/admin separation and recorded history. See `evidence/native-core-2026.10.2`. Full HAOS/Supervisor testing remains pending; the separately created VirtualBox guest stalled under the installed host virtualization stack and is stopped. Physical stationary-person coverage, radio behavior, curtain limits, actual action cancellation and supported Core versions must be certified on an isolated commissioning installation. `tools/check_release.py` continues to block production promotion. Guided pairing/replacement, backups/restore and manual-update policy enforcement are separate unfinished gates; displaying a desired policy does not apply it.

Primary API references reviewed: [Core script engine](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/helpers/script.py), [sun helpers](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/helpers/sun.py), [automation triggers](https://www.home-assistant.io/docs/automation/trigger/) and [building blocks](https://www.home-assistant.io/docs/automation/building-blocks/).
