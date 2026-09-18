"""Run unit/security suites in separate processes because each service owns app.*."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
for service in ('auth-service', 'user-service', 'chat-service', 'message-service'):
    subprocess.run([sys.executable, str(root / 'scripts/test_tokens.py'), service], check=True, cwd=root)
    tests = root / 'services' / service / 'tests'
    if any(tests.glob('test_*.py')):
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(tests), '-v'], check=True, cwd=root)
print('All unit and security suites passed.')
