"""Validation for presentation settings. Lending policy remains separately governed."""
import json
import math
import re

SCOPES={'acquisition','funnel','overview','documents','financials','risk','memo','decision','policy'}
METRICS={'application_count','requested_amount','approved_count','approval_rate','average_decision_days',
         'review_count','held_count','overdue_count','document_count','reviewed_documents',
         'reviewed_fields','blocker_count','open_tasks','dscr','downside_dscr','current_ratio',
         'debt_to_equity','revenue','narrative_count','open_conditions','policy_failures'}

def validate_configuration(scope,data):
    if scope not in SCOPES:
        raise ValueError('Unsupported configuration section')
    if not isinstance(data,dict) or set(data)-{'settings','indicators'}:
        raise ValueError('Configuration contains unsupported properties')
    if len(json.dumps(data,ensure_ascii=False,allow_nan=False))>100000:
        raise ValueError('Configuration exceeds 100,000 characters')
    settings=data.get('settings',{})
    if not isinstance(settings,dict):
        raise ValueError('Settings must be an object')
    indicators=data.get('indicators',[])
    if not isinstance(indicators,list) or len(indicators)>40:
        raise ValueError('At most forty indicators per section are supported')
    ids=set()
    for item in indicators:
        if not isinstance(item,dict):raise ValueError('Indicator must be an object')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',str(item.get('id',''))):raise ValueError('Invalid indicator ID')
        if item['id'] in ids:raise ValueError('Indicator IDs must be unique')
        ids.add(item['id'])
        if not isinstance(item.get('name'),str) or not 1<=len(item['name'].strip())<=120:raise ValueError('Indicator name is required')
        if item.get('type') not in ('KPI','KRI'):raise ValueError('Indicator type must be KPI or KRI')
        if item.get('metric') not in METRICS:raise ValueError('Unsupported metric; executable formulas are not permitted')
        if item.get('direction') not in ('higher','lower'):raise ValueError('Select a metric direction')
        if not isinstance(item.get('visible',True),bool):raise ValueError('Visibility must be boolean')
        for key in ('target','warning','critical'):
            val=item.get(key)
            if val is not None and (isinstance(val,bool) or not isinstance(val,(float,int)) or not math.isfinite(val) or abs(val)>1e18):
                raise ValueError('Targets and thresholds must be finite numbers')
        warning,critical=item.get('warning'),item.get('critical')
        if warning is not None and critical is not None:
            if (item['direction']=='lower' and critical<warning) or (item['direction']=='higher' and critical>warning):
                raise ValueError('Critical threshold must be worse than warning threshold')
    if scope=='risk':
        for key,maximum in (('cashShock',90),('serviceShock',200)):
            val=settings.get(key,0)
            if isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(val) or not 0<=val<=maximum:
                raise ValueError(f'{key} is outside its supported range')
    if scope in ('acquisition','funnel'):
        sla=settings.get('slaDays',5)
        if isinstance(sla,bool) or not isinstance(sla,(int,float)) or not math.isfinite(sla) or not 1<=sla<=365:
            raise ValueError('Operational SLA must be 1-365 days')
    if scope=='memo' and 'chapters' in settings:
        chapters=settings['chapters']
        if not isinstance(chapters,list) or not 1<=len(chapters)<=30 or any(not isinstance(v,str) or not 1<=len(v.strip())<=140 for v in chapters):
            raise ValueError('Supply one to thirty memo chapter titles, each 1-140 characters')
    if scope=='financials' and settings.get('units','base') not in ('base','thousands','millions'):
        raise ValueError('Unsupported financial display units')
    return data
