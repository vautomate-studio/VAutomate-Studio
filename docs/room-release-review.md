# Room controls release review - 6 November 2026

Studio alpha.15 groups room controls into Lights, Comfort, Scenes and Other controls. Readings remain above controls. Existing room membership and shared dashboard publication remain authoritative. Personal 0.2.5 uses matching light/fan vector symbols and puts curtains with Comfort. Native wrappers retain their app identities and signing keys.

Validation: 244 Python tests passed; source/installer checksum checks passed; browser flows and Core contracts passed on 2026.9.4, 2026.10.2 and 2026.10.4. Browser room screenshot was inspected from the CI inert fixture. Existing permission, no-replay, session and pairing tests remain active. Browser code handles unknown device categories without dropping their controls.

These are tested compatibility versions, not a promise of compatibility with every future Core release. The existing release gates and production_ready=false remain correct: physical Android/TV models, real camera streams, device radio pairing, security review and commercial hardware certification are not established by synthetic CI. No upgrade, restore or radio formation is performed by this frontend update.

Personal source and commercial Studio service remain separately configured. The Windows and TV wrappers load the hosted Personal frontend. Studio Android embeds the exact Studio frontend. Source synchronization is enforced by verify_repository.py and build_installer.py.
