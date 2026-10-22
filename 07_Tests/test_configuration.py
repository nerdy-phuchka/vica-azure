from conftest import headers
from app.auth import identity,User
from app.main import app

def payload(version=0):
    return {'expected_version':version,'rationale':'Configure portfolio review indicators',
            'data':{'settings':{'slaDays':5},'indicators':[{'id':'reviews','name':'Cases awaiting review',
            'type':'KRI','metric':'review_count','direction':'lower','visible':True,'warning':5,'critical':10,'target':3}]}}

def test_admin_configuration_and_conflict(client):
    assert client.post('/api/v1/configuration/acquisition',headers=headers(),json=payload()).status_code==403
    saved=client.post('/api/v1/configuration/acquisition',headers=headers('Admin'),json=payload())
    assert saved.status_code==200
    assert saved.json()['version']==1
    assert client.post('/api/v1/configuration/acquisition',headers=headers('Admin'),json=payload()).status_code==409
    result=client.get('/api/v1/configuration',headers=headers()).json()
    assert result['acquisition']['data']['indicators'][0]['type']=='KRI'

def test_configuration_tenant_isolation(client):
    assert client.post('/api/v1/configuration/acquisition',headers=headers('Admin'),json=payload()).status_code==200
    app.dependency_overrides[identity]=lambda:User('other-user',{'Admin'},'other-tenant')
    try:
        assert client.get('/api/v1/configuration',headers=headers('Admin')).json()['acquisition']['version']==0
    finally:app.dependency_overrides.clear()

def test_non_executable_metric_validation(client):
    body=payload();body['data']['indicators'][0]['metric']='__import__("os")'
    assert client.post('/api/v1/configuration/acquisition',headers=headers('Admin'),json=body).status_code==400

def test_policy_baseline_is_separate(client):
    before=client.get('/api/v1/policy',headers=headers()).json()
    body={'expected_version':0,'rationale':'Draft presentation policy configuration','data':{'settings':{'draft':{'rules':[],'status':'approved'}},'indicators':[]}}
    assert client.post('/api/v1/configuration/policy',headers=headers('Admin'),json=body).status_code==200
    assert client.get('/api/v1/policy',headers=headers()).json()==before
