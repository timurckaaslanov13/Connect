import os, sys, unittest
from pathlib import Path
os.environ.update(DATABASE_URL='sqlite://', JWT_SECRET_KEY='test-key-' * 8)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database.connection import Base
from app.database.dependencies import get_db
from app.security.dependencies import get_current_user_id
from app.models.profile import Profile


class FriendshipTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(self.engine)
        with self.session() as db:
            db.add_all([Profile(auth_user_id=i, display_name=f'Person {i}') for i in (1,2,3)])
            db.commit()
        def database():
            with self.session() as db:
                yield db
        self.user = 1
        app.dependency_overrides[get_db] = database
        app.dependency_overrides[get_current_user_id] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_request_accept_remove_and_authorization(self):
        row = self.client.post('/friends/requests', json={'user_id':2}).json()
        self.assertEqual(self.client.post('/friends/requests', json={'user_id':2}).json()['id'], row['id'])
        self.assertEqual(self.client.post(f'/friends/requests/{row["id"]}/accept').status_code, 404)
        self.user = 3
        self.assertEqual(self.client.delete(f'/friends/{row["id"]}').status_code, 404)
        self.user = 2
        self.assertEqual(self.client.get('/friends').json()[0]['direction'], 'incoming')
        self.assertEqual(self.client.post(f'/friends/requests/{row["id"]}/accept').json()['status'], 'accepted')
        self.user = 1
        self.assertEqual(self.client.get('/friends').json()[0]['status'], 'accepted')
        self.assertEqual(self.client.delete(f'/friends/{row["id"]}').status_code, 204)
        self.assertEqual(self.client.get('/friends').json(), [])

    def test_self_and_missing_profile(self):
        self.assertEqual(self.client.post('/friends/requests', json={'user_id':1}).status_code, 400)
        self.assertEqual(self.client.post('/friends/requests', json={'user_id':99}).status_code, 404)
