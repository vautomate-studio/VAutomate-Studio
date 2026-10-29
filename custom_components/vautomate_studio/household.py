"""Reviewed household administration, owner protection and password/session care."""
from __future__ import annotations
import asyncio
from collections import OrderedDict
import re
import secrets
import time
from copy import deepcopy

from .engine import ProductError,text

USERNAME=re.compile(r'[a-z0-9][a-z0-9_.-]{2,47}')
ROLES={'member','administrator','viewer'}


def password(value):
    if not isinstance(value,str) or len(value)<12:
        raise ProductError('invalid_input','Choose a password of at least 12 characters.')
    try:size=len(value.encode('utf-8'))
    except UnicodeError:raise ProductError('invalid_input','This password contains an unsupported character.') from None
    if size>72:
        raise ProductError('invalid_input','This password is too long for the home sign-in provider. Use a shorter passphrase.')
    return value


class Household:
    def __init__(self,adapter,*,clock=time.monotonic):
        self.adapter=adapter;self.clock=clock;self.lock=asyncio.Lock()
        self.reviews=OrderedDict();self.receipts=OrderedDict();self.attempts={}

    def remember(self,cache,key,value,limit=64):
        cache[key]=value
        while len(cache)>limit:cache.popitem(last=False)

    async def identity(self,actor,*,admin=False):
        user=await self.adapter.user(actor.id)
        if not user['active'] or (admin and (not actor.admin or not user['administrator'])):
            raise ProductError('not_allowed','Your current home access does not allow this change.')
        return user

    async def me(self,actor):
        return await self.identity(actor)

    async def people(self,actor):
        await self.identity(actor,admin=True)
        return {'users':await self.adapter.users()}

    def attempt(self,identity):
        now=self.clock()
        self.attempts={key:[t for t in values if now-t<900] for key,values in self.attempts.items() if any(now-t<900 for t in values)}
        if identity not in self.attempts and len(self.attempts)>=256:
            raise ProductError('busy','Account verification is busy. Please try later.')
        values=self.attempts.setdefault(identity,[])
        if len(values)>=5:raise ProductError('rate_limited','Too many account checks. Wait 15 minutes before trying again.')
        values.append(now)

    async def verify(self,actor,current_password):
        if not isinstance(current_password,str) or not 1<=len(current_password)<=256:
            raise ProductError('invalid_input','Enter your current account password to confirm.')
        self.attempt(actor.id)
        await self.adapter.verify(actor.id,current_password)
        self.attempts.pop(actor.id,None)

    async def preview(self,actor,payload):
        current=await self.identity(actor,admin=True)
        if not isinstance(payload,dict):raise ProductError('invalid_input','Review this account change.')
        kind=payload.get('kind')
        if kind=='create':
            if set(payload)-{'kind','name','username','role','local_only'}:raise ProductError('invalid_input','Review this new account.')
            name=text(payload.get('name'),80);username=payload.get('username');role=payload.get('role','member');local=payload.get('local_only',False)
            if not isinstance(username,str) or not USERNAME.fullmatch(username) or role not in ROLES or type(local) is not bool:
                raise ProductError('invalid_input','Choose a name, a simple username and a household role.')
            users=await self.adapter.users()
            if len(users)>=64:raise ProductError('not_supported','This home has reached its household account limit.')
            if any(u['username'] and u['username'].casefold()==username.casefold() for u in users):raise ProductError('username_taken','Choose a different username.')
            plan={'kind':kind,'name':name,'username':username,'role':role,'local_only':local}
        elif kind in {'update','remove','reset_password'}:
            allowed={'kind','user_id','name','role','active','local_only'} if kind=='update' else {'kind','user_id'}
            if set(payload)-allowed or not isinstance(payload.get('user_id'),str):raise ProductError('invalid_input','Choose a household account.')
            target=await self.adapter.user(payload['user_id'])
            if target['owner'] or target['id']==actor.id:
                raise ProductError('protected_account','The owner and your own account are protected here. Use Your account for your password.')
            if kind=='reset_password' and not current['owner']:raise ProductError('not_allowed','Only the home owner can reset someone else’s password.')
            plan={'kind':kind,'user':target}
            if kind=='update':
                role=payload.get('role');active=payload.get('active');local=payload.get('local_only')
                if role not in ROLES or type(active) is not bool or type(local) is not bool:raise ProductError('invalid_input','Review this person’s role and access.')
                plan['changes']={'name':text(payload.get('name'),80),'role':role,'active':active,'local_only':local}
        else:raise ProductError('invalid_input','Choose an account action.')
        nonce=secrets.token_urlsafe(32);self.remember(self.reviews,nonce,{'actor':actor.id,'expires':self.clock()+300,'plan':plan},32)
        return {'approval_nonce':nonce,'expires_in':300,'plan':deepcopy(plan),'writes':False}

    async def approve(self,actor,payload):
        current=await self.identity(actor,admin=True)
        if not isinstance(payload,dict) or set(payload)-{'approval_nonce','current_password','new_password','confirmation'}:raise ProductError('invalid_input','Review this account confirmation.')
        nonce=payload.get('approval_nonce');key=(actor.id,nonce) if isinstance(nonce,str) else None
        if key in self.receipts:return deepcopy(self.receipts[key])
        review=self.reviews.get(nonce) if isinstance(nonce,str) else None
        if not review or review['actor']!=actor.id or review['expires']<self.clock():raise ProductError('approval_expired','Review this account change again.')
        plan=review['plan'];kind=plan['kind']
        if kind in {'create','reset_password'}:password(payload.get('new_password'))
        if kind=='remove' and payload.get('confirmation')!='REMOVE':raise ProductError('confirmation_required','Type REMOVE to confirm removal of this account.')
        if self.lock.locked():raise ProductError('busy','Another account change is being handled. Refresh the household list.')
        async with self.lock:
            current=await self.identity(actor,admin=True)
            await self.verify(actor,payload.get('current_password'))
            if kind!='create':
                target=await self.adapter.user(plan['user']['id'])
                if target!=plan['user'] or target['owner'] or target['id']==actor.id:raise ProductError('state_changed','This person’s access changed. Review it again.')
                if kind=='reset_password' and not current['owner']:raise ProductError('not_allowed','Only the owner can reset this password.')
            del self.reviews[nonce]
            receipt={'kind':kind,'status':'check_required','retry_automatically':False};self.remember(self.receipts,key,receipt)
            try:
                if kind=='create':receipt['user']=await self.adapter.create(plan,payload['new_password'])
                elif kind=='update':await self.adapter.update(plan['user']['id'],plan['changes'])
                elif kind=='remove':await self.adapter.remove(plan['user']['id'])
                else:await self.adapter.change_password(plan['user']['id'],payload['new_password'])
                receipt['status']='saved'
            except asyncio.CancelledError:raise
            except ProductError as error:
                if error.code=='username_taken':receipt['error_code']='username_taken'
            except Exception:pass
            return deepcopy(receipt)

    async def own_password(self,actor,payload):
        await self.identity(actor)
        if not isinstance(payload,dict) or set(payload)!={'current_password','new_password'}:raise ProductError('invalid_input','Enter your current and new passwords.')
        password(payload['new_password'])
        if self.lock.locked():raise ProductError('busy','An account change is already being handled.')
        async with self.lock:
            await self.identity(actor)
            await self.verify(actor,payload['current_password'])
            await self.adapter.change_password(actor.id,payload['new_password'])
        return {'status':'saved','sign_in_again':True}
