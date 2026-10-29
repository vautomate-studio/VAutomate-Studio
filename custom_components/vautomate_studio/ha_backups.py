"""Pinned Home Assistant backup-manager adapter. Export keeps encryption intact."""
from __future__ import annotations

from aiohttp import web
from homeassistant.components.backup.const import DATA_MANAGER
from homeassistant.components.backup.models import Folder

from .engine import ProductError


class HABackups:
    def __init__(self, hass):
        self.hass = hass

    def manager(self):
        manager = self.hass.data.get(DATA_MANAGER)
        if manager is None:
            raise ProductError("not_supported", "Backup storage is not ready on this home.")
        return manager

    async def authorize(self, user_id):
        user = await self.hass.auth.async_get_user(user_id)
        if user is None or not user.is_active or not user.is_admin or user.system_generated:
            raise ProductError("not_allowed", "Administrator access is no longer available.")

    def local(self):
        manager = self.manager()
        supervised = manager.backup_agents.get("hassio.local")
        if supervised and supervised.domain == "hassio" and supervised.unique_id == "local":
            return "hassio.local"
        return next((key for key in sorted(manager.local_backup_agents) if key in manager.backup_agents), None)

    def public(self, item):
        known = self.manager().known_backups.get(item.backup_id)
        return {"backup_id": item.backup_id, "name": item.name[:120], "date": item.date,
                "size": item.size, "protected": item.protected,
                "home_included": item.homeassistant_included, "database_included": item.database_included,
                "core_version": item.homeassistant_version, "app_count": len(item.addons),
                "apps": [{"id": app.slug,"name": app.name or app.slug,"version": app.version} for app in item.addons],
                "folders": sorted(str(folder) for folder in item.folders),
                "complete": not (known.failed_addons or known.failed_folders or known.failed_agent_ids) if known else None}

    async def status(self):
        manager = self.manager()
        local = self.local()
        # No cloud reads or exception details in a household recovery screen.
        backups = []
        failed = False
        if local:
            try:
                backups = [self.public(item) for item in await manager.backup_agents[local].async_list_backups()]
            except Exception:
                failed = True
        event = manager.last_action_event
        return {"state": str(manager.state), "can_create": bool(local) and not failed,
                "storage_attention": failed, "backups": sorted(backups, key=lambda b: b["date"], reverse=True)[:50],
                "last_outcome": str(getattr(event, "state", "")),
                "creation_includes": {"home": True, "database": True, "all_apps": "hassio" in self.hass.config.components,
                                      "folders": [str(f) for f in Folder] if "hassio" in self.hass.config.components else []},
                "export_keeps_encryption": True, "restore_replaces_home": True}

    async def details(self, identity):
        manager = self.manager()
        local = self.local()
        if not local:
            raise ProductError("not_supported", "Local backup storage is unavailable.")
        try:
            backup = await manager.backup_agents[local].async_get_backup(identity)
        except Exception:
            raise ProductError("backup_missing", "This backup is no longer available on the home server.") from None
        if not backup:
            raise ProductError("backup_missing", "This backup is no longer available on the home server.")
        return self.public(backup)

    async def create(self, name, password):
        manager = self.manager()
        local = self.local()
        if not local:
            raise ProductError("not_supported", "Local backup storage is unavailable.")
        supervised = "hassio" in self.hass.config.components
        result = await manager.async_initiate_backup(agent_ids=[local], include_addons=None,
            include_all_addons=supervised, include_database=True, include_folders=list(Folder) if supervised else None,
            include_homeassistant=True, name=name, password=password)
        return result.backup_job_id

    async def receive(self, contents):
        local = self.local()
        if not local:
            raise ProductError("not_supported", "Local backup storage is unavailable.")
        return await self.manager().async_receive_backup(agent_ids=[local], contents=contents)

    async def restore(self, backup, password):
        manager = self.manager()
        await manager.async_restore_backup(backup["backup_id"], agent_id=self.local(), password=password,
            restore_addons=[app["id"] for app in backup["apps"]], restore_database=backup["database_included"],
            restore_folders=[Folder(folder) for folder in backup["folders"]], restore_homeassistant=True)

    async def export(self, identity):
        item = await self.details(identity)
        manager = self.manager()
        local = self.local()
        # The manager, not the caller, resolves the known backup to its local file.
        headers={"Content-Type": "application/x-tar",
            "Content-Disposition": 'attachment; filename="VAutomate-backup-'+identity+'.tar"',
            "Content-Length":str(item["size"]),"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
        if local in manager.local_backup_agents:
            path = manager.local_backup_agents[local].get_backup_path(identity)
            return web.FileResponse(path=path, headers=headers)
        return {"headers":headers,"stream":await manager.backup_agents[local].async_download_backup(identity)}
