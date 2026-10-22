import hashlib
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from .auth import identity,User,require
from .database import Record,get_db,audit,now
from .configuration import SCOPES,validate_configuration

router=APIRouter(prefix='/api/v1/configuration',tags=['Configuration'])

def config_id(tenant,scope):
    return hashlib.sha256((tenant+':'+scope).encode()).hexdigest()

class ConfigurationIn(BaseModel):
    expected_version:int=Field(ge=0)
    data:dict
    rationale:str=Field(min_length=3,max_length=2000)

@router.get('')
def read_configuration(user:User=Depends(identity),db:Session=Depends(get_db)):
    output={}
    for scope in sorted(SCOPES):
        record=db.get(Record,config_id(user.tenant,scope))
        output[scope]={'version':record.version,'data':record.body()['payload']} if record else {'version':0,'data':{}}
    return output

@router.post('/{scope}')
def save_configuration(scope:str,body:ConfigurationIn,user:User=Depends(identity),db:Session=Depends(get_db)):
    require(user,'Admin')
    try:validate_configuration(scope,body.data)
    except (ValueError,TypeError,OverflowError) as exc:raise HTTPException(400,str(exc))
    key=config_id(user.tenant,scope)
    record=db.get(Record,key)
    if (record.version if record else 0)!=body.expected_version:
        raise HTTPException(409,'Configuration changed. Refresh before saving.')
    if record is None:
        record=Record(id=key,kind='configuration',case_id='')
        db.add(record)
    record.set({'tenant':user.tenant,'scope':scope,'payload':body.data,'updated_by':user.subject,
                'updated_at':now().isoformat()+'Z','rationale':body.rationale})
    audit(db,'',user.subject,'configuration.updated',{'tenant':user.tenant,'scope':scope,'rationale':body.rationale})
    db.commit()
    return {'version':record.version,'data':body.data}
