# Repository handover

The intended GitHub repository is **VAutomate-Studio**, private by default. Source preparation does not create a remote repository or account. Complete GitHub sign-in, verify the owner, then create the repository and push `main`. Do not enable customer deployment, broad automation permissions or public visibility as part of routine source setup.

The root `repository.yaml` and nested `installer/vautomate_installer/config.yaml` follow HAOS repository discovery. This does not make a private source repository a public one-click distribution channel. A customer distribution endpoint/repository, immutable images, signing/custody and public installation link require separate release work. Never embed a GitHub token in a customer installation URL.

## CI behavior

- Workflows run tests on pushes/pull requests or explicit manual dispatch.
- Default GitHub token permission is read-only repository contents.
- Checkout does not retain GitHub credentials.
- Actions use commit hashes resolved from their official repositories.
- Native contracts use explicit Core versions, not a floating `stable` tag.
- There is no scheduled updater, image publication, APK signing, remote customer action or deployment job.
- The optional manual production check downloads the current test evidence, then runs the production gate. It intentionally fails while acceptance work is pending.

## Source and release identity

This repository starts at **0.3.0-dev.4**. Previously delivered dev.3 APKs/kits and hosted RC4 releases are unchanged. Historical evidence records keep their actual versions. No GitHub Actions run is claimed until the workflow has executed remotely.

The new source also normalizes a mixed Windows/UTF-8 automation-editor file and verifies that Android, browser, service and installer assets agree. This is a source change, not an automatically installed customer update.

## Ownership and publication

The repository owner must be the GitHub account chosen by the user. An email address alone is not a GitHub owner name. Account creation, email verification and acceptance of account terms remain user steps. No source, keys, credentials, lab disks or customer configuration should be uploaded to an unrelated account.

Local commit identity is for this repository only and must not change global Git preferences. Keep the initial history small and review `git ls-files` and the repository verifier before pushing.
