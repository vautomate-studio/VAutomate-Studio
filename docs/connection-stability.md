# Connection stability hardening

Working source after RC4; published APK/ZIP downloads remain unchanged. The isolated HAOS Studio lab serves the updated client. The personal dashboard and installed personal APK have not been changed.

- A 15-second connection/authentication deadline recovers stalled handshakes.
- Authenticated connections send a Home Assistant protocol ping every 20 seconds. A missing matching pong after 10 seconds closes the connection and starts recovery.
- Retry delay grows from 1.5 seconds to 24 seconds, plus up to one second of jitter, until authentication succeeds.
- Replacing a connection immediately marks it disconnected and rejects pending requests. Old socket callbacks cannot overwrite the new connection state.
- Manual recovery cancels older retry timers. Sign-out cancels connection, heartbeat, refresh and retry timers.
- Interrupted or uncertain device commands are rejected, never queued or replayed. Read the device's confirmed status before a manual retry.

Deterministic regression tests cover handshake stalls, unmatched heartbeat replies, healthy heartbeat replies, stale callbacks, retry cancellation, command non-replay and sign-out cleanup. Existing authentication/transport and responsive showroom tests also pass.

The actual HAOS 18.4 / Core 2026.10.4 lab passed three browser disconnect/reconnect cycles without another sign-in or losing its shared dashboard. The running server's delivered client hash matches this source; real ping/pong works. The browser test sends no device commands and reports no uncaught page errors. Evidence: `work/haos-lab/stability-result.json` in the workspace. These are bounded tests, not an extended uptime soak or physical Android certification.

The saved private cold baseline predates this frontend fix. Restoring that baseline also restores its older client; reapply the reviewed source patch before repeating recovery tests. No automatic deployment or updater has been added.
