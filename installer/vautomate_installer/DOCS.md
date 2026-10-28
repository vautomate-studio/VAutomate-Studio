# Installation and safety

Start performs installation and may restart Core. Use an independent development server only. Confirm an independently stored backup and explicitly enable candidate evaluation. The app runs manually; it has no web interface or automatic updater.

After success open `/vautomate-studio/index.html` on the server, sign in, then choose **Set up this home**. Existing owner creation remains an installer task. Pairing, recovery, physical acceptance and production release signing remain unfinished.

Requested permissions: writable Home Assistant configuration for the Studio component; Core API access to activate it; Supervisor `homeassistant` role to validate/restart Core. No host network, hardware or Docker socket is requested. Stop/uninstall the commissioning app after handover. The Studio integration runs independently afterwards.

See the repository-level README for preservation, backups, failure recovery and release limits.
