import uuid
from conftest import headers
from app.database import Session,add

def create(client,synthetic=True):
    response=client.post('/api/v1/applications',headers={**headers(),'Idempotency-Key':str(uuid.uuid4())},
      json={'borrower_name':'Test SME','requested_amount':'250000','synthetic':synthetic})
    assert response.status_code==201,response.text
    return response.json()['id']

def read(client,id):
    return client.get('/api/v1/applications/'+id,headers=headers()).json()

def test_idempotency_and_tenant_case_isolation(client):
    h={**headers(),'Idempotency-Key':'fixed'}; body={'borrower_name':'Test SME','requested_amount':'1'}
    first=client.post('/api/v1/applications',headers=h,json=body)
    again=client.post('/api/v1/applications',headers=h,json=body)
    assert first.json()['id']==again.json()['id']
    assert client.post('/api/v1/applications',headers=h,json={**body,'requested_amount':'2'}).status_code==409
    assert client.get('/api/v1/applications/'+first.json()['id'],headers=headers(subject='outsider')).status_code==404
    assert client.get('/api/v1/applications').status_code==401

def test_role_and_stale_version(client):
    case=create(client)
    assert client.post(f'/api/v1/applications/{case}/members',headers=headers(),json={'subject':'xxy','expected_version':1}).status_code==403
    assert client.post(f'/api/v1/applications/{case}/transitions',headers=headers(),
       json={'action':'submit','expected_version':999,'rationale':'Test stale request'}).status_code==409

def test_real_policy_pending_blocks_progression(client):
    case=create(client,False)
    result=client.post(f'/api/v1/applications/{case}/assessments',headers=headers(),json={
       'period':'FY 2025','currency':'SAR','confirm_base_currency_and_annual_service':True,'expected_version':read(client,case)['version']})
    assert result.status_code==200,result.text
    assert 'Policy configuration is not approved' in result.json()['blockers']
    data=read(client,case)
    assert client.post(f'/api/v1/applications/{case}/transitions',headers=headers(),json={
        'action':'submit','rationale':'Submit proposal','expected_version':data['version']}).status_code==409

def test_full_synthetic_review_and_conditional_decision(client):
    case=create(client)
    for subject in ('demo-reviewer','demo-approver'):
        data=read(client,case)
        assert client.post(f'/api/v1/applications/{case}/members',headers=headers('Admin'),json={
           'subject':subject,'expected_version':data['version']}).status_code==200
    # Fixtures are expert-reviewed source records, not simulated external-provider responses.
    with Session() as db:
        for kind in ('registration','financial_statements','bank_statement'):
            add(db,'document',case,{'filename':kind+'.txt','document_type':kind,'state':'processed','reviewed':True,
                'reviewed_by':'demo-analyst','sha256':'fixture','pages':[{'page':1,'text':'Fixture evidence'}]})
        db.commit()
    for name,value in {'legal_name':'Test SME','registration_number':'12345','revenue':'2000000',
                       'cash_available':'300000','existing_debt_service':'100000','proposed_debt_service':'100000'}.items():
        field=client.post(f'/api/v1/applications/{case}/fields',headers=headers(),json={
             'name':name,'value':value,'rationale':'Expert confirmed synthetic input'}).json()
        result=client.post(f'/api/v1/applications/{case}/fields/{field["id"]}/review',headers=headers(),json={
             'value':value,'rationale':'Base currency and period reviewed','expected_version':field['version']})
        assert result.status_code==200,result.text
    for category in ('legal','compliance','fraud','field_visit'):
        data=read(client,case)
        result=client.post(f'/api/v1/applications/{case}/clearances',headers=headers('Reviewer'),json={
           'category':category,'status':'clear','rationale':'Synthetic specialist review completed','expected_version':data['version']})
        assert result.status_code==200,result.text
    data=read(client,case)
    result=client.post(f'/api/v1/applications/{case}/assessments',headers=headers(),json={
        'period':'FY 2025','currency':'SAR','confirm_base_currency_and_annual_service':True,'expected_version':data['version']})
    assert result.status_code==200,result.text
    assert result.json()['blockers']==[]
    for role,action in [('Analyst','submit'),('Reviewer','review_accept')]:
        result=client.post(f'/api/v1/applications/{case}/transitions',headers=headers(role),json={
            'action':action,'rationale':'Independent workflow check','expected_version':read(client,case)['version']})
        assert result.status_code==200,result.text
    result=client.post(f'/api/v1/applications/{case}/decisions',headers=headers('Approver'),json={
       'decision':'conditional','rationale':'Synthetic decision with condition','conditions':['Signed agreement'],
       'expected_version':read(client,case)['version']})
    assert result.status_code==200,result.text
    condition=result.json()['conditions'][0]['id']
    assert client.post(f'/api/v1/applications/{case}/conditions/{condition}/fulfil',headers=headers('Reviewer'),json={
       'evidence':'Synthetic executed agreement received','expected_version':result.json()['version']}).status_code==200
    assert client.post(f'/api/v1/applications/{case}/fields',headers=headers(),json={
       'name':'revenue','value':'1','rationale':'Cannot alter decided snapshot'}).status_code==409
    report=client.get(f'/api/v1/applications/{case}/reports?format=docx',headers=headers())
    assert report.status_code==200 and report.content.startswith(b'PK')

def test_document_upload_worker_and_reprocessing_invalidation(client):
    import asyncio
    from app.worker import claim,run_job
    case=create(client)
    upload=client.post(f'/api/v1/applications/{case}/documents',headers=headers(),files={'file':('evidence.txt','English and عربي document evidence'.encode(),'text/plain')})
    assert upload.status_code==202,upload.text
    job=claim(); assert job
    asyncio.run(run_job(job))
    detail=read(client,case)
    doc=detail['documents'][0]
    assert doc['state']=='processed'
    assert 'not configured' in doc['warning']
    duplicate=client.post(f'/api/v1/applications/{case}/documents',headers=headers(),files={'file':('evidence.txt','English and عربي document evidence'.encode(),'text/plain')})
    assert duplicate.json()['duplicate']
    assert client.get(f'/api/v1/applications/{case}/documents/{doc["id"]}/content',headers=headers(subject='outsider')).status_code==404
