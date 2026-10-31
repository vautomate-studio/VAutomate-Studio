# VAutomate commissioning installer

Development version 0.4.0-alpha.5. This is not a certified customer release. The bundled service is complete source, not a downloader. Published RC4 artifacts and the personal home are separate.

## Intended installation

1. An installer prepares an independent HAOS server, creates its owner account and keeps an independently stored, tested backup. Customer setup does not require a developer token.
2. Add the VAutomate app repository, install **VAutomate Studio Installer**, and review the requested configuration-folder/Core API permissions. A public repository and signed production images have not been published yet; there is no public one-click link at this stage.
3. Confirm the independent backup. For an isolated development server only, explicitly allow the candidate. Start the installer. Start is the install action; it is manual-only and exposes no web or network port.
4. The installer verifies its bundled files, checks the platform, saves existing Studio code, installs only `custom_components/vautomate_studio`, validates the configuration, restarts Core if the code changed, and creates the Studio integration if missing. Existing integration settings and shared-home data remain in place. Device controls are never enabled automatically.
5. Open `/vautomate-studio/index.html`, sign in with the home account, and choose **Set up this home**. Name the home, suggest rooms from existing assignments or add them manually, select devices, choose Home buttons, review and publish. Suggestions do not pair, rename, move or operate devices.
6. Home Care â†’ Installation status provides a local status record. Use the fleet register to track many independent installations. No phone credentials or remote-access tokens are part of the record.

On an empty Core configuration with Studio preloaded, `/local/vautomate-setup/index.html` can create the first owner and finish platform setup inside VAutomate. This path was tested using a disposable fresh Core configuration on the existing HAOS lab. Initial HAOS provisioning and preloading the package remain installer tasks; a factory image and full fresh-HAOS acceptance have not been delivered. See [first-home evidence](../docs/first-home-onboarding.md).

Radio provisioning, Matter pairing, customer invitations/recovery, physical-device certification, remote support consent, notification delivery, signed release images and disaster recovery are separate unfinished release gates. This kit does not make them available.

## Local lab preparation

Run `python tools/build_installer.py` from the commercial source directory to create the payload manifest and ZIP. Copy the `vautomate_installer` folder to the lab's local apps folder, reload the store and install the local app. This is an installer/developer procedure, not the promised public one-click customer experience.

The app cannot run at boot. It has no device access, Docker socket, host networking, ingress, arbitrary command execution or API proxy. It needs writable Home Assistant configuration access to install its component and the documented `homeassistant` Supervisor role to check/restart Core. The Core proxy is privileged; do not expose this installer to customers or reuse its token elsewhere.

## Recovery

Before restart, a failed configuration check restores the previous component directory automatically. Existing Studio source is also copied under the installer's private `component-backups` folder. These source copies are **not full Home Assistant backups**. After an uncertain restart or activation failure the installer records `needs_installer_attention`; it does not loop restarts or roll back live configuration automatically. Repeating an unchanged successful installation does not restart Core or create another integration entry.

The OS-backed installation lock is released when the process exits. Its `V` marker remains intentionally; never delete it during an active installation. An explicit retry reads the prior journal and can recover its own interrupted directory rename. Legacy or unrecognized locks fail for installer review. If copied source was never started, an explicit retry can request one restart and reconcile the running version. There is no automatic restart loop. Restore a full home from the independent backup when necessary; actual disaster restoration must be tested separately.

## Local inventory

```text
python tools/fleet_register.py --database fleet.sqlite --import-record VAutomate-installation-ID.json
python tools/fleet_register.py --database fleet.sqlite
```

Keep this database private. It contains installation identifiers, software versions, counts and commissioning results, not credentials, customer names, server addresses or device lists. It performs no network access or remote rollout. Local control has no commercial expiry.

## Release process

Approve a hardware/platform matrix, perform a restore drill and physical acceptance, review authorization and licensing, publish a VAutomate-owned source repository and immutable signed images, then make the public repository link. Supported architectures listed in this development app are build targets; only an actual tested architecture may be marketed as supported. The release checker still blocks production promotion. Do not set `production_ready` to true to bypass unfinished checks.
