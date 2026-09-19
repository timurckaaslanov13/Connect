import json
import time
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketState
from sqlalchemy import or_, select
from app.database.connection import SessionLocal
from app.models.call import Call
from app.security.dependencies import get_current_user_id
from app.security.jwt import decode_access_token, get_access_token_expiry
from app.clients.chat_service import check_user_chat_membership
from app.api.websocket import SocketAuth
from app.websocket.user_events import user_events, user_connections
import asyncio

router = APIRouter(tags=['calls'])


class Signal(BaseModel):
    type: Literal['call.invite', 'call.answer', 'call.ice', 'call.end']
    call_id: UUID
    chat_id: int = Field(gt=0)
    target_id: int = Field(gt=0)
    media: Literal['audio', 'video'] = 'audio'
    sdp: str | None = Field(default=None, max_length=64000)
    candidate: dict | None = None
    reason: Literal['ended', 'declined', 'missed', 'busy', 'failed'] = 'ended'


def record_call(data, sender, status):
    with SessionLocal() as db:
        row = db.get(Call, str(data.call_id))
        if status == 'ringing' and row is None:
            row = Call(id=str(data.call_id), chat_id=data.chat_id, caller_id=sender, callee_id=data.target_id, media=data.media)
            db.add(row)
        if row is None:
            return
        row.status = status
        if status == 'active':
            row.answered_at = datetime.now(timezone.utc)
        if status in ('ended', 'declined', 'missed', 'busy', 'failed'):
            row.ended_at = datetime.now(timezone.utc)
        db.commit()


async def relay(data: Signal, sender: int):
    redis = user_events.redis
    if redis is None or not user_events.ready:
        raise ValueError('Сервис звонков временно недоступен')
    if sender == data.target_id:
        raise ValueError('Нельзя позвонить себе')
    key = 'connect:call:' + str(data.call_id)
    if data.type == 'call.invite':
        if not data.sdp:
            raise ValueError('Отсутствует предложение соединения')
        for member in (sender, data.target_id):
            if not await check_user_chat_membership(data.chat_id, member):
                raise ValueError('Нет доступа к этому чату')
        state = json.dumps({'caller': sender, 'callee': data.target_id, 'chat': data.chat_id, 'phase': 'ringing'})
        if not await redis.set(key, state, nx=True, ex=120):
            raise ValueError('Этот звонок уже существует')
        await run_in_threadpool(record_call, data, sender, 'ringing')
    else:
        old = await redis.get(key)
        if not old:
            raise ValueError('Звонок завершён')
        state = json.loads(old)
        if set((sender, data.target_id)) != set((state['caller'], state['callee'])) or data.chat_id != state['chat'] or state['phase'] == 'ended':
            raise ValueError('Нет доступа к звонку')
        if data.type == 'call.answer':
            if sender != state['callee'] or state['phase'] != 'ringing' or not data.sdp:
                raise ValueError('Нельзя принять этот звонок')
            state['phase'] = 'active'
        elif data.type == 'call.end':
            state['phase'] = 'ended'
        if data.type != 'call.ice':
            changed = await redis.eval("if redis.call('GET',KEYS[1]) == ARGV[1] then redis.call('SET',KEYS[1],ARGV[2],'EX',ARGV[3]); return 1 else return 0 end", 1, key, old, json.dumps(state), 7200 if state['phase'] == 'active' else 60)
            if not changed:
                raise ValueError('Состояние звонка изменилось')
            await run_in_threadpool(record_call, data, sender, 'active' if data.type == 'call.answer' else data.reason)
    event = data.model_dump(mode='json') | {'sender_id': sender}
    await user_events.send(data.target_id, event)


@router.websocket('/ws/events')
async def event_socket(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    tracked = {}
    try:
        async with asyncio.timeout(5):
            auth = SocketAuth.model_validate_json(await websocket.receive_text())
            user_id = decode_access_token(auth.token)
            expiry = get_access_token_expiry(auth.token)
        await user_connections.connect(user_id, websocket, accepted=True)
        await websocket.send_json({'type': 'ready'})
        async with asyncio.timeout(max(0, expiry - time.time())):
            while websocket.application_state == WebSocketState.CONNECTED:
                raw = await websocket.receive_text()
                if len(raw) > 80000:
                    await websocket.close(code=1009)
                    return
                data = None
                try:
                    if json.loads(raw).get('type') == 'ping':
                        await websocket.send_json({'type': 'pong'})
                        continue
                    data = Signal.model_validate_json(raw)
                    await relay(data, user_id)
                    if data.type in ('call.invite', 'call.answer'):
                        tracked[str(data.call_id)] = data
                    elif data.type == 'call.end':
                        tracked.pop(str(data.call_id), None)
                except Exception as error:
                    # Never return raw validation errors containing tokens, SDP or internal details.
                    await websocket.send_json({'type': 'call.error', 'call_id': str(data.call_id) if data else None, 'message': str(error) if type(error) is ValueError else 'Не удалось обработать сигнал звонка'})
    except WebSocketDisconnect:
        pass
    except (ValueError, TimeoutError, KeyError):
        await websocket.close(code=1008)
    finally:
        if user_id is not None:
            user_connections.disconnect(user_id, websocket)
            for data in tracked.values():
                try:
                    await relay(data.model_copy(update={'type': 'call.end', 'reason': 'ended', 'sdp': None, 'candidate': None}), user_id)
                except Exception:
                    pass


def load_calls(user_id):
    with SessionLocal() as db:
        rows = db.scalars(select(Call).where(or_(Call.caller_id == user_id, Call.callee_id == user_id)).order_by(Call.created_at.desc()).limit(100))
        now = datetime.now(timezone.utc)
        result = []
        for r in rows:
            created = r.created_at.replace(tzinfo=timezone.utc) if r.created_at.tzinfo is None else r.created_at
            status = 'missed' if r.status == 'ringing' and (now-created).total_seconds() > 120 else r.status
            result.append(dict(id=r.id, chat_id=r.chat_id, caller_id=r.caller_id, callee_id=r.callee_id, media=r.media, status=status, created_at=r.created_at, answered_at=r.answered_at, ended_at=r.ended_at))
        return result


@router.get('/calls')
async def call_history(user_id: int = Depends(get_current_user_id)):
    return await run_in_threadpool(load_calls, user_id)


@router.get('/calls/config')
def call_config(user_id: int = Depends(get_current_user_id)):
    from app.core.config import settings
    import hmac, hashlib, base64
    servers = [{'urls': 'stun:stun.l.google.com:19302'}]
    if settings.turn_urls and settings.turn_secret:
        username = f'{int(time.time()) + 3600}:{user_id}'
        credential = base64.b64encode(hmac.new(settings.turn_secret.encode(), username.encode(), hashlib.sha1).digest()).decode()
        servers.append({'urls': settings.turn_urls.split(','), 'username': username, 'credential': credential})
    return {'iceServers': servers}
