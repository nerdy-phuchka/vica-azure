#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  python3 - <<'PY'
from pathlib import Path
import secrets
text=Path('02_Configuration/.env.example').read_text()
for placeholder in ('replace-with-a-long-local-only-secret','replace-with-another-long-local-secret','replace-with-an-independent-long-secret'):
    text=text.replace(placeholder,secrets.token_hex(32))
Path('.env').write_text(text)
Path('.env').chmod(0o600)
print('Created .env; use DEV_AUTH_TOKEN locally. Do not share it.')
PY
fi
docker compose config --quiet
docker compose up --build -d
printf '%s\n' 'Open http://127.0.0.1:3000 ; local identity is for synthetic cases.'
