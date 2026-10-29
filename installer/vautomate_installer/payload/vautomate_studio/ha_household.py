"""Scoped HA authentication adapter. Passwords and credential hashes are never exported."""
from homeassistant.auth.const import GROUP_ID_ADMIN,GROUP_ID_USER,GROUP_ID_READ_ONLY
from homeassistant.auth.providers import homeassistant as provider_module
from .engine import ProductError


GROUPS={'administrator':GROUP_ID_ADMIN,'member':GROUP_ID_USER,'viewer':GROUP_ID_READ_ONLY}


class HAHousehold:
    def __init__(self,hass):self.hass=hass

    def provider(self):
        try:return provider_module.async_get_provider(self.hass)
        except RuntimeError:raise ProductError('not_supported','This home needs a compatible account sign-in provider.') from None

    def public(self,user):
        if user.system_generated:raise ProductError('protected_account','System accounts cannot be changed here.')
        credentials=next((c for c in user.credentials if c.auth_provider_type=='homeassistant'),None)
        return {'id':user.id,'name':user.name or 'Home member','owner':user.is_owner,'administrator':user.is_admin,
                'role':next((role for role,identity in GROUPS.items() if {g.id for g in user.groups}=={identity}),'custom'),'active':user.is_active,'local_only':user.local_only,'username':credentials.data.get('username') if credentials else None,
                'password_supported':credentials is not None}

    async def user(self,identity):
        user=await self.hass.auth.async_get_user(identity)
        if user is None:raise ProductError('account_missing','This household account is no longer available.')
        return self.public(user)

    async def users(self):
        return [self.public(user) for user in await self.hass.auth.async_get_users() if not user.system_generated]

    async def verify(self,identity,password):
        item=await self.user(identity)
        if not item['active'] or not item['username']:raise ProductError('not_supported','Password confirmation is unavailable for this account.')
        try:await self.provider().async_validate_login(item['username'],password)
        except provider_module.InvalidAuth:raise ProductError('invalid_password','Your current password could not be verified.') from None

    async def create(self,plan,password):
        provider=self.provider();user=None;added=False
        try:
            try:await provider.async_add_auth(plan['username'],password)
            except provider_module.InvalidUser:raise ProductError('username_taken','Choose another username.') from None
            added=True
            user=await self.hass.auth.async_create_user(plan['name'],group_ids=[GROUPS[plan['role']]],local_only=plan['local_only'])
            credentials=await provider.async_get_or_create_credentials({'username':plan['username']})
            await self.hass.auth.async_link_user(user,credentials)
            return self.public(user)
        except BaseException:
            # Only resources created by this request may be removed on partial failure.
            if user is not None:await self.hass.auth.async_remove_user(user)
            if added:
                try:await provider.async_remove_auth(plan['username'])
                except provider_module.InvalidUser:pass
            raise

    async def update(self,identity,changes):
        user=await self.hass.auth.async_get_user(identity)
        if user is None or user.system_generated or user.is_owner:raise ProductError('protected_account','This account is protected.')
        await self.hass.auth.async_update_user(user,name=changes['name'],group_ids=[GROUPS[changes['role']]],is_active=changes['active'],local_only=changes['local_only'])
        # Refresh grants and local-only policy on every existing device by ending sessions.
        self.revoke(user)

    def revoke(self,user):
        self.revoke_tokens(tuple(user.refresh_tokens.values()))

    def revoke_tokens(self,tokens):
        for token in tokens:self.hass.auth.async_remove_refresh_token(token)

    async def remove(self,identity):
        user=await self.hass.auth.async_get_user(identity)
        if user is None or user.system_generated or user.is_owner:raise ProductError('protected_account','This account is protected.')
        await self.hass.auth.async_remove_user(user)

    async def change_password(self,identity,password):
        item=await self.user(identity)
        if not item['username']:raise ProductError('not_supported','This account uses another sign-in provider.')
        await self.provider().async_change_password(item['username'],password)
        user=await self.hass.auth.async_get_user(identity)
        if user is not None:
            # Let the requesting client receive its acknowledgement, then close all sessions.
            self.hass.loop.call_later(.5,self.revoke_tokens,tuple(user.refresh_tokens.values()))
