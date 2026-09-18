"""Generate local development secrets without overwriting existing configuration."""
import argparse
from pathlib import Path
import secrets


def initialize(output: Path, test_ports: bool):
    values = {name: secrets.token_hex(32) for name in (
        'JWT_SECRET_KEY', 'INTERNAL_API_KEY', 'AUTH_DB_PASSWORD', 'USER_DB_PASSWORD',
        'CHAT_DB_PASSWORD', 'MESSAGE_DB_PASSWORD')}
    if test_ports:
        for i, service in enumerate(('AUTH', 'USER', 'CHAT', 'MESSAGE')):
            values[service + '_PORT'] = str(18000 + i)
            values[service + '_DB_PORT'] = str(15432 + i)
    with output.open('x', encoding='utf-8') as file:
        file.write('\n'.join(f'{key}={value}' for key, value in values.items()) + '\n')
    print(f'Created {output}; secrets were not printed. Keep this file out of Git.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('.env'))
    parser.add_argument('--test-ports', action='store_true')
    args = parser.parse_args()
    initialize(args.output, args.test_ports)
