# Security and customer data

VAutomate Studio is an evaluation build. It is not approved for customer deployment. Do not expose the commissioning installer or enable evaluation controls on a production home.

Do not commit credentials, signing keys, native vault exports, `.storage`, customer backups, server addresses, camera URLs, GPS information, unredacted diagnostics or lab disks. The repository verifier checks common credential formats and private file types; it is not a complete security audit.

Use one independent server per home. Studio backend operations enforce administrator checks, managed-entity selection and the account's existing Home Assistant permissions. Hiding navigation does not prevent a Home Assistant account from using other APIs it is permitted to access. Restricted guests and a customer-only gateway remain release work.

Report vulnerabilities privately to the repository owner. Do not put exploitable details or customer information in public issues. No remote diagnostics or support access is enabled by this repository.

The installer receives privileged Core API access and configuration write access. Run it only for explicit commissioning, keep an independent backup, and stop/uninstall the installer app afterwards. The installed service runs independently.

GitHub Actions test source only. They cannot deploy to homes, publish images, sign APKs or perform customer updates. Production signing material belongs in separately controlled custody and is never included here.
