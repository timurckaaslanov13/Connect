"""Check PostgreSQL migration round trips in NEW temporary databases only.

Requires an already running isolated Docker Compose project whose name ends -check.
Usage: python scripts/check_migrations.py --project connect-check
Existing service databases and user data are never migrated or dropped by this script.
"""
import argparse
import re
import subprocess

REMOTE_CHECK = r'''
import os
import subprocess
import sys
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.core.config import settings

name = 'migration_check_' + uuid.uuid4().hex
source = make_url(settings.database_url)
admin = create_engine(source, isolation_level='AUTOCOMMIT')
with admin.connect() as connection:
    connection.execute(text('CREATE DATABASE "' + name + '"'))
try:
    env = dict(os.environ, DATABASE_URL=source.set(database=name).render_as_string(hide_password=False))
    for args in [('upgrade', 'head'), ('check',), ('downgrade', 'base'), ('upgrade', 'head'), ('check',)]:
        subprocess.run([sys.executable, '-m', 'alembic', *args], env=env, check=True)
finally:
    with admin.connect() as connection:
        connection.execute(text('DROP DATABASE "' + name + '"'))
    admin.dispose()
print('PASS: upgrade/check/downgrade/upgrade/check; temporary database removed')
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='connect-check')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*-check', args.project):
        parser.error('Use an isolated project whose name ends with -check')
    for service in ('auth', 'user', 'chat', 'message'):
        print(f'Checking {service} migrations', flush=True)
        subprocess.run(['docker', 'exec', '-i', f'{args.project}-{service}-service-1', 'python', '-'],
                       input=REMOTE_CHECK, text=True, check=True)
