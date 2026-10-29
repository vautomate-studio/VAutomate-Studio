# Studio API v1

Transport: the server's authenticated `/api/websocket` connection. After normal HA authentication, send:

```json
{"id":1,"type":"vautomate_studio/v1/request","operation":"bootstrap","payload":{}}
```

Responses use normal HA result/error envelopes. An unsupported product operation returns `not_supported`; it is never forwarded to an arbitrary Core or Supervisor command.

| Operation | Access | Purpose |
| --- | --- | --- |
| `bootstrap` | Authenticated active home account | API/service/Core versions, compatibility status, role, shared layout, filtered capabilities/states, routines and feature flags |
| `snapshot` | Authenticated active home account | Current curated states and shared revision |
| `discover` | Administrator | Read existing supported entities and room/device metadata for commissioning |
| `layout/preview` | Administrator | Validate a proposed Studio layout without writing |
| `layout/publish` | Administrator | Compare revision, validate, persist only the Studio document, then expose it to all clients |
| `command` | HA entity read/control permission | Explicit supported action, or room light/fan/switch master action |
| `routine/save`, `routine/remove` | Administrator | Compare revision and persist a bounded time/day routine |
| `bundles/list` | Active home account | Inert versioned suggestions; no automatic creation |
| `bundles/preview` | Administrator | Validate selected devices/schedule and return a five-minute account-bound review nonce; no persisted routine or device action |
| `bundles/approve` | Same administrator | Revalidate the reviewed plan/revision and save an independent copy; paused unless explicitly enabled; repeated submission returns its receipt |
| `history` | HA entity read permission | Up to 24 hours for one managed entity, at most 2,000 returned points, no state attributes |
| `camera/snapshot` | HA camera read permission | Bounded JPEG/PNG/WebP snapshot, no camera URLs or tokens |
| `activity` | Filtered member / administrator | Redacted in-memory recent command/layout/routine activity |
| `care` | Administrator | Installation checks and pending certification status |
| `backups/status` | Administrator | Local encrypted-copy metadata and backup-manager state; no cloud reads or passwords |
| `backups/preview` | Administrator | Inert five-minute review for encrypted creation or selected restoration |
| `backups/approve` | Same administrator | One explicitly approved create/restore dispatch; no automatic replay; password stays transient |
| `accounts/me` | Active household account | Own safe account/role details; no credentials or tokens |
| `accounts/list` | Administrator | Household identities and roles; system accounts excluded |
| `accounts/preview` | Administrator | Account-bound five-minute create/edit/remove/reset review without writing |
| `accounts/approve` | Same administrator and current password | Reviewed create/edit/remove; only owner can reset another password; owner/self/system access protected |
| `accounts/password` | Active account and own current password | Change only its own password and end pre-existing sessions |

Recovery uses three fixed HTTP routes. `POST /api/vautomate_studio/v1/backups/export` requires administrator authentication and prepares a one-use HttpOnly download cookie. `GET /api/vautomate_studio/v1/backups/download/{backup_id}` consumes that cookie, rechecks current administrator status and streams the original archive. No account credential, password or download capability appears in the URL. `POST /api/vautomate_studio/v1/backups/import` requires administrator authentication and streams one multipart `.tar` file into local backup storage; it never restores automatically. See [recovery scope](recovery.md).

Command example (use a fresh sufficiently long random request identity and server-adjusted expiry):

```json
{"request_id":"unique-request-identity-123","expires_at":1793092815,"entity_id":"light.pendant","action":"turn_off","data":{},"expected_state":"on"}
```

The example expiry is illustrative; it must be generated afresh. Commands expire within 30 seconds. No cloud/offline command queue is supported. An accepted action is not a guarantee of physical state: the UI waits for subsequent readings. Lost/late replies require checking current state; they are not automatically retried. Duplicate identities with different payloads fail. Running/recent command reservations are bounded, and capacity exhaustion fails closed rather than evicting still-valid reservations. Cache reservations are process-local; a Core restart is a reason to re-read state, not replay old requests.

Alarm code data is forwarded only to the selected alarm action. Fingerprints are keyed, process-local HMACs; payloads/codes are not retained in the idempotency cache. Service failures return safe product errors. Activity is bounded memory data, not a durable security audit archive.

Home layout schema: `name`, `subtitle`, `rooms` (unique ID/name and explicit entity IDs), and at most four `quick_actions` pointing to distinct scenes or input-boolean modes. Unknown top-level fields and arbitrary service parameters are rejected. Revision checks prevent silently overwriting another editor's changes.

The HA adapter is the only module importing HA internals. API v1 is the compatibility boundary for clients. A future breaking product contract needs v2 or a documented migration. No currently certified Core range is implied by this API version.
