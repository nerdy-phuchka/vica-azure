"""Initial schema bootstrap. v0.1 has no upgrade migrations; take a backup before later releases."""
from .config import settings
from .database import init_db
if __name__=='__main__':
    settings().validate_runtime()
    init_db()
    print('Initial schema created/verified (v0.1.0).')
