"""Run per service: python scripts/test_tokens.py auth-service"""
import os
from pathlib import Path
import sys
import time
import unittest

service = sys.argv.pop(1)
if service not in ('auth-service', 'user-service', 'chat-service', 'message-service'):
    raise SystemExit('Unknown service')
os.environ.update(DATABASE_URL='sqlite://', JWT_SECRET_KEY='test-key-' * 8,
                  INTERNAL_API_KEY='internal-test-' * 4, USER_SERVICE_URL='http://user.test',
                  CHAT_SERVICE_URL='http://chat.test')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'services' / service))
import jwt
from app.security.jwt import decode_access_token, get_access_token_expiry
from app.core.config import settings


class TokenTests(unittest.TestCase):
    def encode(self, payload, key=None):
        return jwt.encode(payload, key or settings.jwt_secret_key, algorithm='HS256')

    def test_valid(self):
        expiry = int(time.time()) + 60
        token = self.encode({'sub': '7', 'exp': expiry})
        self.assertEqual(decode_access_token(token), 7)
        self.assertEqual(get_access_token_expiry(token), expiry)

    def test_expired_and_missing_claims(self):
        for payload in [{'sub': '7'}, {'exp': time.time() + 60}, {'sub': '7', 'exp': time.time() - 1}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                decode_access_token(self.encode(payload))

    def test_invalid_subjects(self):
        for subject in ['0', '-1', 'abc', None, 7, [], '1.5']:
            with self.subTest(subject=subject), self.assertRaises(ValueError):
                decode_access_token(self.encode({'sub': subject, 'exp': time.time() + 60}))

    def test_invalid_expiry(self):
        for expiry in [None, 'invalid', float('inf'), float('nan'), True, str(int(time.time()) + 60)]:
            with self.subTest(expiry=expiry), self.assertRaises(ValueError):
                decode_access_token(self.encode({'sub': '7', 'exp': expiry}))

    def test_wrong_signature(self):
        with self.assertRaises(ValueError):
            decode_access_token(self.encode({'sub': '7', 'exp': time.time() + 60}, 'other-key-' * 8))


if __name__ == '__main__':
    unittest.main()
