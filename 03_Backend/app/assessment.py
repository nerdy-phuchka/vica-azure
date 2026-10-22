from fastapi import HTTPException
from .database import records, add, audit, emit
from .finance import calculate, amortisation
from .policy import load_policy, evaluate
from .transactions import summarise
from datetime import date
from .config import settings

FINAL_STATES={'approved','conditional','declined','deferred'}


def invalidate(db,case,reason):
    data=case.body()
    if data['status'] in FINAL_STATES:
        raise HTTPException(409,'Decision snapshot is locked. Create a new application/review for new evidence.')
    data['data_revision']=data.get('data_revision',0)+1
    data['current_assessment']=None
    data['status']='data_review'
    data['credit_reviewer']=None
    case.set(data)
    audit(db,case.id,'system','assessment.invalidated',{'reason':reason})


def build_assessment(db,case,user,period,currency):
    data=case.body()
    if data['status'] in FINAL_STATES:
        raise HTTPException(409,'Decided case is immutable')
    fields=records(db,'field',case.id)
    selected=[f for f in fields if f.body().get('reviewed') and f.body().get('active')]
    values={f.body()['name']:f.body()['value'] for f in selected}
    financial=calculate(values)
    schedule=amortisation(data['requested_amount'],data['proposed_annual_rate'],data['tenor_months']) if data.get('proposed_annual_rate') is not None else None
    policy=load_policy(data['synthetic'])
    checks=evaluate(policy,financial['metrics'])
    exceptions=[r.body() for r in records(db,'exception',case.id)]
    for check in checks:
        exception=next((e for e in exceptions if e['rule_id']==check['rule_id'] and
            e['data_revision']==data['data_revision'] and e['policy_version']==policy['version']),None)
        if exception and check['outcome']=='fail' and not check['hard_stop']:
            check.update(outcome='exception_approved',exception=exception)
    docs=records(db,'document',case.id)
    blockers=[]
    for date_field in ('licence_expiry','incorporation_date'):
        if values.get(date_field):
            try:
                day=date.fromisoformat(values[date_field])
                if date_field=='licence_expiry' and day<date.today():blockers.append('Reviewed licence has expired')
                if date_field=='incorporation_date' and day>date.today():blockers.append('Incorporation date is in the future')
            except ValueError:
                blockers.append(f'{date_field}: confirm calendar and normalise to ISO Gregorian date')
    transactions=[t.view() for t in records(db,'transaction',case.id)]
    transaction_summary=summarise(transactions)
    if transaction_summary['unreviewed_count']:
        blockers.append('Statement schedule contains unreviewed transactions')
    for task in records(db,'task',case.id):
        if task.body().get('blocking') and task.body().get('status')!='resolved':
            blockers.append('Open blocking task: '+task.body()['title'])
    if policy['status'] not in ('approved','demo'):
        blockers.append('Policy configuration is not approved')
    if policy['status']=='approved' and not policy.get('approved_by'):
        blockers.append('Policy approval evidence is missing')
    if data['synthetic'] and policy['status']!='demo':
        blockers.append('Synthetic applications require demonstration policy')
    for kind in policy.get('documents',[]):
        if not any(d.body().get('document_type')==kind and d.body().get('reviewed') for d in docs):
            blockers.append(f'Reviewed document required: {kind}')
    if any(d.body().get('state')!='processed' or not d.body().get('reviewed') for d in docs):
        blockers.append('All uploaded documents must be processed and reviewed')
    for name in ('legal_name','registration_number','revenue','cash_available','existing_debt_service','proposed_debt_service'):
        if not values.get(name):
            blockers.append(f'Reviewed field required: {name}')
    for category in ('legal','compliance','fraud','field_visit'):
        clearance=data.get('clearances',{}).get(category,{})
        if clearance.get('status') not in ('clear','not_applicable'):
            blockers.append(f'Reviewer clearance required: {category}')
        elif category in ('legal','compliance','fraud') and clearance.get('reviewer')==user.subject:
            blockers.append(f'Specialist clearance must be independent of preparing officer: {category}')
    for check in checks:
        if check['outcome'] not in ('pass','exception_approved'):
            blockers.append(f"Policy {check['rule_id']}: {check['outcome']}")
    metrics=financial['metrics']
    if metrics['dscr'] is None:
        blockers.append('Repayment capacity cannot be established from current inputs')
    snapshot={'data_revision':data['data_revision'],'period':period,'currency':currency,
        'input_units':'Reviewed base currency; annual cash/debt service',
        'fields':[{**f.view()} for f in selected], 'values':values,
        'documents':[{'id':d.id,'sha256':d.body()['sha256'],'type':d.body().get('document_type'),
                      'reviewed_by':d.body().get('reviewed_by')} for d in docs],
        'policy':policy, 'checks':checks,'financial':financial,
        'clearances':data.get('clearances',{}),
        'notes':[n.view() for n in records(db,'note',case.id)],
        'transaction_summary':transaction_summary,
        'proposed_schedule':schedule,
        'borrower_name':data['borrower_name'],'requested_amount':data['requested_amount'],
        'product':data['product'],'purpose':data['purpose'],
        'blockers':blockers,'recommendation':'refer' if blockers else 'ready_for_independent_review',
        'prepared_by':user.subject,'rating':'Not available — no approved credit model configured',
        'model_version':{'rating':'not_configured','ai_deployment':settings().azure_openai_deployment or 'not_configured',
                         'extraction_prompt':'vca-extraction-v1','document_api':'2024-11-30'},
        'synthetic':data['synthetic']}
    result=add(db,'assessment',case.id,snapshot)
    data.update(current_assessment=result.id,status='credit_assessment',prepared_by=user.subject,credit_reviewer=None)
    case.set(data)
    audit(db,case.id,user.subject,'assessment.created',{'assessment_id':result.id})
    emit(db,case.id,'assessment.completed',{'assessment_id':result.id,'recommendation':snapshot['recommendation']})
    return result


def current_assessment(db,case):
    from .database import Record
    data=case.body()
    record=db.get(Record,data.get('current_assessment')) if data.get('current_assessment') else None
    if not record or record.body()['data_revision']!=data['data_revision']:
        raise HTTPException(409,'Run an assessment for the current evidence first')
    return record
