"""Create PostgreSQL custom-format backups without printing database credentials.
Stop application writers first for a consistent backup across all four databases.
Usage: python scripts/backup.py --project connect --output backups
"""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def backup(project, output):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', project):
        raise ValueError('Invalid Compose project name')
    folder = Path(output) / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder.mkdir(parents=True, exist_ok=False, mode=0o700)
    manifest = {'project': project, 'created_at': datetime.now(timezone.utc).isoformat(), 'files': {}}
    for service in ('auth', 'user', 'chat', 'message'):
        container = f'{project}-{service}-db-1'
        target = folder / f'{service}.dump'
        with target.open('xb') as stream:
            subprocess.run(['docker', 'exec', container, 'pg_dump', '-U', f'{service}_user', '-d', f'{service}_db', '-Fc', '--no-owner', '--no-acl'], stdout=stream, check=True)
        target.chmod(0o600)
        with target.open('rb') as stream:
            subprocess.run(['docker', 'exec', '-i', container, 'pg_restore', '--list'], stdin=stream, stdout=subprocess.DEVNULL, check=True)
        manifest['files'][target.name] = {'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'Backup complete: {folder.resolve()}')
    return folder

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='connect')
    parser.add_argument('--output', default='backups')
    args = parser.parse_args()
    backup(args.project, args.output)
