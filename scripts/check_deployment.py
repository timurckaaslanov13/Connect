"""Validate the production Compose layout without printing resolved secrets."""
import json
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = dict(os.environ, CONNECT_DOMAIN='connect.example.com', ACME_EMAIL='ops@example.com')
for key in ('AUTH_DB_PASSWORD','USER_DB_PASSWORD','CHAT_DB_PASSWORD','MESSAGE_DB_PASSWORD','JWT_SECRET_KEY','INTERNAL_API_KEY'):
    env[key] = 'validation-only-' + 'x'*40
result = subprocess.run(['docker','compose','-f','docker-compose.yml','-f','docker-compose.production.yml','config','--format','json'], cwd=root, env=env, capture_output=True, text=True, check=True)
config = json.loads(result.stdout)
for name, service in config['services'].items():
    if name != 'gateway':
        assert not service.get('ports'), f'{name} publishes a port'
    assert service.get('restart') == 'unless-stopped', name
ports = config['services']['gateway']['ports']
assert {(p['target'],p.get('protocol','tcp')) for p in ports} == {(80,'tcp'),(443,'tcp'),(443,'udp')}
print('PASS: only HTTPS gateway publishes ports; all services restart automatically')
