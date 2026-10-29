"""Reviewed administrator backup operations; no arbitrary paths or API proxy."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
import hashlib
import json
import re
import secrets
import time

from .engine import ProductError, text

IDENTITY = re.compile(r"[A-Za-z0-9_-]{1,128}")


def admin(actor):
    if not actor.admin:
        raise ProductError("not_allowed", "Only a home administrator can manage recovery.")


def backup_id(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise ProductError("invalid_input", "Choose a saved backup.")
    return value


def fingerprint(backup):
    return hashlib.sha256(json.dumps(backup, sort_keys=True).encode()).hexdigest()


class HomeBackups:
    def __init__(self, adapter, *, clock=time.monotonic):
        self.adapter = adapter
        self.clock = clock
        self.reviews = OrderedDict()
        self.receipts = OrderedDict()
        self.downloads = OrderedDict()
        self.lock = asyncio.Lock()

    def remember(self, cache, key, value, limit=64):
        cache[key] = value
        while len(cache) > limit:
            cache.popitem(last=False)

    async def status(self, actor):
        admin(actor)
        return await self.adapter.status()

    async def preview(self, actor, payload):
        admin(actor)
        if not isinstance(payload, dict) or set(payload) - {"kind", "backup_id", "name"}:
            raise ProductError("invalid_input", "Review the backup request.")
        kind = payload.get("kind")
        if kind == "create":
            plan = {"kind": "create", "name": text(payload.get("name", "VAutomate home backup"), 80)}
            status = await self.adapter.status()
            if status["state"] != "idle" or not status["can_create"]:
                raise ProductError("busy", "Recovery is busy or local backup storage is unavailable. Refresh its status.")
            plan["includes"] = status["creation_includes"]
        elif kind == "restore":
            item = await self.adapter.details(backup_id(payload.get("backup_id")))
            if not item["home_included"]:
                raise ProductError("not_supported", "This backup does not include the home configuration.")
            plan = {"kind": "restore", "backup": item}
        else:
            raise ProductError("invalid_input", "Choose create or restore.")
        nonce = secrets.token_urlsafe(32)
        self.remember(self.reviews, nonce, {"actor": actor.id, "expires": self.clock() + 300, "plan": plan}, 32)
        return {"approval_nonce": nonce, "expires_in": 300, "plan": plan, "writes": False}

    async def approve(self, actor, payload):
        admin(actor)
        if not isinstance(payload, dict) or set(payload) - {"approval_nonce", "password", "password_saved", "confirmation", "independent_copy"}:
            raise ProductError("invalid_input", "Review the recovery confirmation.")
        nonce = payload.get("approval_nonce")
        if not isinstance(nonce, str):
            raise ProductError("approval_expired", "Review this backup operation again.")
        key = (actor.id, nonce)
        if key in self.receipts:
            return dict(self.receipts[key])
        review = self.reviews.get(nonce)
        if not review or review["actor"] != actor.id or review["expires"] < self.clock():
            raise ProductError("approval_expired", "Review this backup operation again.")
        plan = review["plan"]
        password = payload.get("password")
        if plan["kind"] == "create":
            if not isinstance(password, str) or not 12 <= len(password) <= 256 or payload.get("password_saved") is not True:
                raise ProductError("invalid_input", "Choose a recovery password of at least 12 characters and confirm you will keep it separately.")
        elif payload.get("confirmation") != "RESTORE" or payload.get("independent_copy") is not True:
            raise ProductError("confirmation_required", "Save an independent backup first, then type RESTORE to confirm replacement of this home.")
        elif plan["backup"]["protected"] and (not isinstance(password, str) or not 1 <= len(password) <= 256):
            raise ProductError("invalid_input", "Enter this backup's recovery password.")
        elif password is not None and (not isinstance(password, str) or len(password) > 256):
            raise ProductError("invalid_input", "Check the recovery password.")
        if self.lock.locked():
            raise ProductError("busy", "A recovery request is already being handled. Check its status.")
        async with self.lock:
            # Refresh identity immediately before privileged dispatch.
            await self.adapter.authorize(actor.id)
            if key in self.receipts:
                return dict(self.receipts[key])
            if plan["kind"] == "restore":
                current = await self.adapter.details(plan["backup"]["backup_id"])
                if fingerprint(current) != fingerprint(plan["backup"]):
                    raise ProductError("state_changed", "The backup changed. Review it again before restoring.")
            # Consume before dispatch. A timeout/cancellation is not permission to repeat.
            del self.reviews[nonce]
            receipt = {"kind": plan["kind"], "status": "check_required", "retry_automatically": False}
            self.remember(self.receipts, key, receipt)
            try:
                if plan["kind"] == "create":
                    identity = await self.adapter.create(plan["name"], password)
                    receipt.update(status="started", job_id=backup_id(identity))
                else:
                    await self.adapter.restore(plan["backup"], password or None)
                    receipt.update(status="requested")
            except asyncio.CancelledError:
                raise
            except Exception as error:
                # Never return manager exceptions: some contain paths or passwords.
                code = getattr(error, "error_code", "")
                if code in {"password_incorrect", "backup_not_found"}:
                    receipt["error_code"] = code
                return dict(receipt)
            finally:
                password = None
            return dict(receipt)

    async def export(self, actor, identity):
        admin(actor)
        await self.adapter.authorize(actor.id)
        return await self.adapter.export(backup_id(identity))

    async def prepare_download(self, actor, identity):
        admin(actor)
        identity = backup_id(identity)
        await self.adapter.authorize(actor.id)
        await self.adapter.details(identity)
        token = secrets.token_urlsafe(32)
        self.remember(self.downloads, token, {"actor": actor.id, "backup_id": identity, "expires": self.clock()+300}, 32)
        return token

    async def download(self, token, identity):
        record = self.downloads.pop(token, None) if isinstance(token, str) else None
        if not record or record["backup_id"] != backup_id(identity) or record["expires"] < self.clock():
            raise ProductError("download_expired", "Request a fresh backup download.")
        await self.adapter.authorize(record["actor"])
        return await self.adapter.export(identity)
