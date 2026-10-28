# Development

Changes must preserve existing Home Assistant configuration and the independent personal VAutomate app. Use a disposable commissioning server with synthetic devices first. Never copy a real household's configuration, radio credentials or account tokens into this repository.

Run:

```text
python tools/verify_repository.py
python tools/test_engine.py
npm ci
npx playwright install chromium
npm test
npm run test:blueprints
python tools/build_installer.py
python tools/verify_repository.py
```

The source intentionally includes frontend copies for the service, Android shell and installer payload. Keep them identical. Regenerate the installer after approved service changes. `verify_repository.py` catches stale copies and common private data.

Manual customer updates are a product requirement. Changes to compatibility checks, access control, backup behavior or execution policy require explicit review and acceptance evidence. Keep default evaluation controls read-only. Proposed automation bundles must remain inert until approved and paused by default.

Record the actual environment and scope of tests. Simulation, live synthetic-device checks and physical-device certification are different evidence. `python tools/check_release.py` intentionally fails until all required production acceptance records are present.
