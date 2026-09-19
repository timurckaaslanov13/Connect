import os,sys,unittest,json
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock,patch
os.environ.update(DATABASE_URL='sqlite://',JWT_SECRET_KEY='test-key-'*8,INTERNAL_API_KEY='test-internal-'*4,CHAT_SERVICE_URL='http://chat.test')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api.calls import Signal,relay
from app.api import calls


class MemoryRedis:
    def __init__(self): self.values={}
    async def set(self,key,value,nx=False,ex=None):
        if nx and key in self.values: return False
        self.values[key]=value
        return True
    async def get(self,key): return self.values.get(key)
    async def eval(self,script,n,key,old,new,expiry):
        if self.values.get(key)!=old: return 0
        self.values[key]=new
        return 1


class CallTests(unittest.IsolatedAsyncioTestCase):
    async def test_offer_answer_end_and_spoofing(self):
        signal=Signal(type='call.invite',call_id=uuid4(),chat_id=1,target_id=2,sdp='offer')
        with patch.object(calls.user_events,'redis',MemoryRedis()),patch.object(calls.user_events,'ready',True),patch.object(calls.user_events,'send',AsyncMock()) as send,patch.object(calls,'check_user_chat_membership',AsyncMock(return_value=True)),patch.object(calls,'record_call'):
            await relay(signal,1)
            self.assertEqual(send.call_args.args[0],2)
            answer=signal.model_copy(update={'type':'call.answer','target_id':1,'sdp':'answer'})
            with self.assertRaises(ValueError): await relay(answer,3)
            await relay(answer,2)
            await relay(signal.model_copy(update={'type':'call.end'}),1)
            with self.assertRaises(ValueError): await relay(answer,2)

    async def test_nonmember_cannot_invite(self):
        with patch.object(calls.user_events,'redis',MemoryRedis()),patch.object(calls.user_events,'ready',True),patch.object(calls,'check_user_chat_membership',AsyncMock(return_value=False)):
            with self.assertRaises(ValueError):
                await relay(Signal(type='call.invite',call_id=uuid4(),chat_id=1,target_id=2,sdp='offer'),1)


class EventSocketTests(unittest.TestCase):
    def test_heartbeat_does_not_enter_call_signalling(self):
        import time
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        app = FastAPI()
        app.include_router(calls.router)
        with patch.object(calls, 'decode_access_token', return_value=1), patch.object(calls, 'get_access_token_expiry', return_value=time.time()+60), patch.object(calls, 'relay', AsyncMock()) as relay_mock:
            with TestClient(app).websocket_connect('/ws/events') as ws:
                ws.send_json({'type': 'auth', 'token': 'test'})
                self.assertEqual(ws.receive_json()['type'], 'ready')
                ws.send_json({'type': 'ping'})
                self.assertEqual(ws.receive_json(), {'type': 'pong'})
                ws.send_text('not json')
                self.assertEqual(ws.receive_json()['type'], 'call.error')
                ws.send_json({'type': 'ping'})
                self.assertEqual(ws.receive_json(), {'type': 'pong'})
            relay_mock.assert_not_called()
