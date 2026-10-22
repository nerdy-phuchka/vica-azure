import os
import sys
import tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'03_Backend'))
temp=tempfile.TemporaryDirectory()
os.environ.update(APP_MODE='local',DATABASE_URL='sqlite:///'+str(Path(temp.name)/'test.db'),
    LOCAL_STORAGE_PATH=str(Path(temp.name)/'files'),DEV_AUTH_ENABLED='true',
    DEV_AUTH_TOKEN='test-only-long-secret-token-12345',POLICY_FILE=str(root/'02_Configuration/policy.pending.json'),
    LOS_CALLBACK_URL='',AZURE_DOCUMENT_ENDPOINT='',AZURE_OPENAI_ENDPOINT='',AZURE_SEARCH_ENDPOINT='',
    AZURE_SERVICEBUS_NAMESPACE='',SCANNER_MODE='disabled-local',DEV_PROXY_SECRET='')
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base,engine

@pytest.fixture(autouse=True)
def reset():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

def headers(role='Analyst',subject=None):
    return {'Authorization':'Bearer test-only-long-secret-token-12345',
            'X-Dev-Role':role,'X-Dev-User':subject or 'demo-'+role.lower()}
