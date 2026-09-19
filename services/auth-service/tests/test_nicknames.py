import os
os.environ.update(DATABASE_URL='sqlite://', JWT_SECRET_KEY='test-key-'*8)
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database.connection import Base
from app.models.user import User
from app.schemas.user import UserRegister
from app.services.auth import register_user
from app.exceptions.auth import UserAlreadyExistsError
from app.api.auth import directory

class NicknameTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db=Session(self.engine)
    def tearDown(self):
        self.db.close()
        self.engine.dispose()
    def test_case_insensitive_uniqueness_and_public_search(self):
        first=register_user(self.db, UserRegister(email='one@example.com',username=' @Marina ',password='password123'))
        self.assertEqual(first.username,'marina')
        with self.assertRaises(UserAlreadyExistsError):
            register_user(self.db, UserRegister(email='two@example.com',username='MARINA',password='password123'))
        rows=directory(q='@MAR',current_user=first,db=self.db)
        self.assertEqual(rows,[{'auth_user_id':first.id,'username':'marina'}])
        self.assertNotIn('email',rows[0])
        self.assertEqual(directory(q='one@example.com',current_user=first,db=self.db),[])
    def test_database_enforces_case_insensitive_index(self):
        self.db.add_all([User(email='a@example.com',username='Alice',password_hash='hash'),User(email='b@example.com',username='alice',password_hash='hash')])
        with self.assertRaises(IntegrityError):self.db.commit()
    def test_validation_and_literal_underscore_search(self):
        from pydantic import ValidationError
        for name in ['ab','with space','hello%','имя']:
            with self.assertRaises(ValidationError):UserRegister(email='a@example.com',username=name,password='password123')
        self.db.add_all([User(email='a@example.com',username='ab_cd',password_hash='hash'),User(email='b@example.com',username='abxcd',password_hash='hash')]);self.db.commit()
        rows=directory(q='ab_',current_user=None,db=self.db)
        self.assertEqual([r['username'] for r in rows],['ab_cd'])
