# Shared interaction states

Personal and Studio use the same `shared/ui-states.js` and CSS. Run `python tools/sync_ui_states.py` to synchronize canonical editions; package their canonical assets afterwards.

| State | Required behavior |
| --- | --- |
| Empty | Explain the next setup or selection action. Never invent devices. |
| Loading | Keep the current view; show feedback for requests beyond 1.5 seconds. |
| Error | Explain the cause and offer a safe recovery action. |
| Offline | Keep last readings visible; connection status identifies stale information. Controls cannot queue writes. |
| Slow | After 8 seconds explain the delay; never replay an uncertain write. |
| No results | Offer clear search or connection setup rather than a dead end. |
| Permission | Explain the required administrator access and who can change it. Server permission checks remain authoritative. |
| Session expired | Capture safe editor drafts before credential teardown; offer sign in and explicit restoration. |
| Validation | Place an accessible error beside its exact input, focus the first invalid field, clear on correction. |
| Success | Confirm the completed action and explain the next step where appropriate. A sent device request is not confirmation that hardware responded. |

Drafts are scoped by edition, server origin, native profile and user. They are session-only with a 24-hour expiry, not cloud backups. Passwords, tokens, keys and alarm codes are omitted. Restore is an explicit editor action and must never toggle a control. Structured automation drafts preserve conditions/actions rather than only visible text fields. Secret inputs must be entered again. A different browser session does not inherit a sessionStorage draft.

Read-only retry is user initiated. Failed or timed-out mutations show **Check current status**, never a replay button. A return online refreshes reads only. Partial native integration setup must reconcile its own journal before continuation.

Validation evidence: `tests/ui-states-browser.cjs` exercises all ten states using inert DOM and controlled time, privacy filtering, per-user isolation and no restoration actuation. The full Studio browser suite covers actual editor integration. Personal full-index checks are performed separately in its local test workspace. Physical Android/TV and network outage acceptance still require device testing.

Alpha.7 adds feedback hosted in the active modal top layer, concurrent-request ownership, preserved input help text, camel-case credential filtering and editor-specific keys. Untouched editors cannot overwrite an existing draft. Complete room models retain selections hidden by search; restoration never publishes a layout. Personal rooms retain cached readings and disabled actuators during disconnection.
