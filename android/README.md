# VAutomate Studio Android customer app

Development source **0.4.0-alpha.2**, package `co.vautomate.customer`, version code 8, minimum Android API 31 and target API 36. Physical Android certification remains pending.

This independent package does not upgrade the personal `co.vautomate.home` app or the Studio Preview. It uses its bundled VAutomate frontend and the versioned Studio service on the configured local/remote server. A missing service produces setup guidance, not a fallback to the Home Assistant frontend.

Remembered authentication uses the native encrypted vault. Browser sessions keep credentials in memory. No password or signing key is included in this repository. Local/remote endpoint selection, branding and frontend assets are included; the root repository verifier checks that bundled customer assets match the canonical frontend.

## Build

Use JDK 17, SDK Platform 36 and compatible official Android build tools. The Gradle project and `tools/build-unsigned.py` are supplied. The Python builder takes `--java-home`, `--android-jar`, `--build-tools`, `--r8-jar` and `--output`. The R8 version and checksum are recorded in `tools/r8-toolchain.json`.

A generated unsigned APK must be signed and verified using controlled signing custody. Never commit a keystore, password or vault export. CI does not sign or deploy Android apps. Prior local dev.3 APKs are separate artifacts; the local alpha build has separate build/signature evidence and is not a physical-device certification.

See the root README, security policy and commercial acceptance requirements. A successful source build does not certify cameras, notifications, physical devices, Android versions or customer recovery.
