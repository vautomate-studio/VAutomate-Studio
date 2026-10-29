# Backups and recovery

Development workflow introduced in 0.4.0-alpha.2. Production acceptance remains separate.

Administrators open **Home Care → Backups & recovery**. Members have no recovery entry, and backend authorization rejects their requests independently of the menu.

## Save a protected home

Choose **Create encrypted backup**, review the name and included contents, choose a recovery password of at least 12 characters, repeat it and confirm that it will be stored separately. HAOS copies the home configuration, database, installed apps and supported server folders through its backup manager. Container installations include their supported home/database scope. VAutomate does not enable a backup schedule, change retention, delete existing copies or install updates.

The request starts a job; success is not claimed until the backup manager finishes and the copy appears. A lost reply is never automatically retried. Refresh status to reconcile it. Approval receipts are bounded and process-local; a restart invalidates old reviews and does not replay them.

**Save a separate copy** streams the original archive, preserving encryption. The browser does not load the full archive into JavaScript memory. Android uses its document picker and streams to the chosen destination. The download URL contains only a backup identifier. Its five-minute authorization is in an HttpOnly, SameSite=Strict cookie scoped to that one download path; it is consumed on use and the administrator's current status is checked again. It is not an account token. File exports and recovery passwords are not included in diagnostic reports or GitHub evidence.

## Import and restore

**Import saved copy** streams an exported `.tar` archive into local backup storage, with an upload limit below 4 GB including the multipart envelope. Import does not restore or replace the home. The platform validates the archive. Imported copies can then be reviewed like existing backups.

**Review restore** shows the saved name, date, configuration/history scope and included apps. Restoring replaces current data and can change sign-in to the accounts saved in that copy. An administrator must confirm an independent current backup, type **RESTORE**, and supply the saved copy's password. The review expires after five minutes, belongs to the approving administrator and is rechecked against current backup metadata. Device commands are not replayed after a restore or reconnect.

Recovery cannot be promised without the exported archive and its password. Keep both independently, in different safe locations. A copy saved only on the gateway is insufficient if the gateway fails. A download interrupted or cancelled after authorization needs a fresh explicit export request; a partial destination file may remain.

## Verified scope

On 29 October 2026, the synthetic HAOS 18.4 / Core 2026.10.4 lab created an encrypted 21,248,000-byte home/database/app/folder backup. An identical archive was downloaded outside the VM. A cold VM checkpoint was retained, the synthetic home name was changed, and one reviewed restore was requested. After the expected connection interruption, the saved shared layout, control setting and paused automations matched their original values. Supervisor remained healthy and automatic updates stayed disabled. The exported archive was also re-imported without an automatic restore or layout change.

Actual household-member API requests were denied for listing, review, approval, import and export; anonymous export was rejected. A live browser download matched the independently saved archive hash. Browser fixtures cover review, password mismatch/cleanup, import, typed restore confirmation and the phone layout. Native Java policy checks and the signed APK build pass. No physical Android document-picker acceptance is claimed.

See [real restore evidence](../evidence/recovery-alpha2/backup-drill-result.json) and [browser evidence](../evidence/recovery-alpha2/browser-recovery-result.json). No personal-server settings, users, rooms or devices were changed.

A fresh replacement-gateway import-and-restore drill, spare physical hardware, disaster handover and recovery with unavailable storage remain production gates. A same-lab restore is not blanket certification of every hardware or platform version.

The adapter follows the pinned [Core backup manager interfaces](https://github.com/home-assistant/core/tree/2026.10.4/homeassistant/components/backup) and [Supervisor backup implementation](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/hassio/backup.py). There is no generic Supervisor API proxy in the customer interface.
