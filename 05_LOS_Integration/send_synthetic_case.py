"""Run against the local API: DEV_AUTH_TOKEN=... python send_synthetic_case.py."""
import json
import os
import urllib.request
import uuid

url=os.getenv('VCA_URL','http://127.0.0.1:8000').rstrip('/')
payload={'borrower_name':'Namaa Demo Trading / نماء للتجارة','requested_amount':'250000',
         'product':'working_capital','currency':'SAR','purpose':'Synthetic inventory financing',
         'los_reference':'LOS-DEMO-001','synthetic':True}
key=str(uuid.uuid4())
headers={'Authorization':'Bearer '+os.environ['DEV_AUTH_TOKEN'],'X-Dev-User':'demo-analyst',
         'X-Dev-Role':'Analyst','Idempotency-Key':key,'Content-Type':'application/json'}
data=json.dumps(payload,ensure_ascii=False).encode()
for attempt in range(2):
    request=urllib.request.Request(url+'/api/v1/applications',data=data,headers=headers)
    with urllib.request.urlopen(request) as response:
        result=json.load(response)
        print(json.dumps({'attempt':attempt+1,'id':result['id'],'status':result['status']},ensure_ascii=False))
print('Both attempts must return the same application ID. Admin can add demo-reviewer and demo-approver as case members.')
