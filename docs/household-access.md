# Household accounts and access

Development workflow introduced in 0.4.0-alpha.3. Each home has its own accounts and server; no household credentials are collected in the multi-home inventory.

## Administrator workflow

Open **Home Care → Household access**. Add a person with a name, unique username, role and optional local-connection restriction. The three standard roles are:

- **Home member:** uses permitted home controls and sees the published shared dashboard.
- **View only:** sees permitted states/history without operating devices. This uses the backend's read-only permission group, not a visual-only switch.
- **Administrator:** manages the published home and household accounts, including other administrators. Assign deliberately.

Review the proposed account before adding its password. Confirm every management action with your own current password. The account password must have at least 12 characters and fit the backend's 72-byte UTF-8 hashing limit; longer values are rejected rather than silently truncated. Share the sign-in privately. The person can then choose their own password from **Your account**.

Account edits compare the reviewed identity/role/access with the current server state, expire after five minutes and belong to the reviewing administrator. Pausing access, changing a role or removing an account ends its existing sessions. Account removal also removes its sign-in credentials. It does not delete rooms or routines; existing routine execution rechecks the saved owner's access before dispatch.

The owner cannot be removed, paused or demoted through this workflow. Administrators cannot remove or alter their own access here. System-generated accounts are excluded and protected again in the adapter. Only the owner may reset another person's password, matching the platform's stronger account-reset boundary. Resetting a password also ends prior sessions.

Changing a standard role replaces that account's existing groups. A pre-existing custom-group account is identified as custom; it requires a deliberate standard-role choice. Local-only access follows the server's network/authentication policy, which must be validated with the actual remote-access/proxy configuration; it is not a physical-presence detector.

## Personal password and session care

Every active household account can choose **Your account → Change my password**, supply its current password and repeat a strong new password. The old sessions are revoked, while a new sign-in created after the change is not accidentally revoked. Password values are cleared after submission, closing and cancellation. Failed password confirmations are bounded to five attempts per 15 minutes; successful verified management does not consume that failure allowance.

No password, credential hash, refresh token or connection history is returned in a household listing or stored in a review/receipt. Receipts are bounded and process-local. A lost account-change reply is not automatically replayed. Refresh the household list and check access before making another decision.

## Tested scope

On 29 October 2026, a fresh disposable Core 2026.10.4 fixture running on the isolated HAOS lab passed actual account creation, duplicate-approval handling, wrong-password rejection, view-only shared layout/capabilities, denied view-only device control, promotion/demotion, pause/re-enable, removal, self password change, owner reset and old-session closure. Old passwords and removed accounts could not sign in. The temporary account was removed and the fixture's original dashboard and read-only setting were restored. Main-lab and personal-home accounts were not changed.

Automated policy/adapter checks cover owner/self protection, current identity checks, expired/stale reviews, partial-create cleanup without deleting pre-existing credentials, hash-length limits, bounded failures and revoking only the pre-existing session snapshot. Browser fixtures cover phone layout, password cleanup, role choices and absence of administrator entry points for members.

See [actual account lifecycle](../evidence/household-alpha3/household-live-result.json), [fresh first-owner setup](../evidence/household-alpha3/first-owner-live-result.json) and [browser checks](../evidence/household-browser.json).

Lost-owner-password recovery, lost-MFA recovery, invitation delivery, physical Android account flows and customer handover remain production gates. Do not describe member password resets as complete disaster or owner-account recovery. Current commissioning still needs an independently stored encrypted backup and a tested support procedure.
