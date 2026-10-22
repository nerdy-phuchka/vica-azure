import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import timedelta
import httpx
from sqlalchemy import or_, update
from .config import settings
from .database import Session, Job, Record, now, init_db, add, audit, emit
from .storage import get, credential
from .providers import extract, interpret, index_pages
from .transactions import parse_schedule

log=logging.getLogger('vca.worker')


def claim():
    with Session() as db:
        candidate=db.query(Job).filter(Job.state.in_(['queued','running']),Job.available_at<=now()).order_by(Job.available_at).first()
        if not candidate:
            return None
        # Compare-and-swap claim; a crashed worker's lease expires after fifteen minutes.
        lease=now()+timedelta(minutes=15)
        result=db.execute(update(Job).where(Job.id==candidate.id,Job.available_at==candidate.available_at,
                                          Job.state.in_(['queued','running'])).values(
                           state='running',available_at=lease,attempts=Job.attempts+1))
        db.commit()
        return candidate.id if result.rowcount else None


async def process_document(target):
    with Session() as db:
        doc=db.get(Record,target)
        if not doc or doc.body().get('state')=='processed':
            return
        data=doc.body()
    content=await asyncio.to_thread(get,data['storage_key'])
    pages=await extract(data['filename'],content)
    if sum(len(p['text']) for p in pages)>2_000_000:
        raise ValueError('Extracted text exceeds prototype limit')
    interpreted=await interpret(pages)
    transactions=await asyncio.to_thread(parse_schedule,data['filename'],content)
    with Session() as db:
        doc=db.get(Record,target)
        # Do not leak duplicate fields across a retry. All extracted data commits atomically.
        data=doc.body()
        data.update(pages=pages,state='processed',document_type=interpreted['document_type'],
                    language=interpreted['language'],warning=interpreted.get('warning',''),error='')
        doc.set(data)
        for f in interpreted['fields']:
            add(db,'field',doc.case_id,{**f,'document_id':doc.id,'reviewed':False,'active':False,
                                      'origin':'azure_ai','original_value':f['value']})
        for transaction in transactions:
            add(db,'transaction',doc.case_id,{**transaction,'document_id':doc.id})
        audit(db,doc.case_id,'worker','document.processed',{'document_id':doc.id})
        emit(db,doc.case_id,'document.processed',{'document_id':doc.id})
        db.commit()
    try:
        await asyncio.to_thread(index_pages,doc.case_id,target,pages)
    except Exception:
        # Search is optional: committed OCR and manual review remain available.
        with Session() as db:
            doc=db.get(Record,target)
            data=doc.body(); data['search_warning']='Search indexing failed; case-local evidence fallback active'; doc.set(data); db.commit()


async def send_callback(target):
    s=settings()
    if not s.los_callback_url or len(s.los_callback_secret)<24:
        raise ValueError('LOS callback configuration missing or secret too short')
    with Session() as db:
        event=db.get(Record,target)
        body={k:v for k,v in event.view().items() if k not in ('delivery','version')}
    payload=json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()
    stamp=str(int(time.time()))
    signature=hmac.new(s.los_callback_secret.encode(),stamp.encode()+b'.'+payload,hashlib.sha256).hexdigest()
    async with httpx.AsyncClient(timeout=20,follow_redirects=False) as client:
        response=await client.post(s.los_callback_url,content=payload,
            headers={'Content-Type':'application/json','X-VCA-Timestamp':stamp,'X-VCA-Signature':signature,'X-VCA-Event-ID':target})
        response.raise_for_status()
    with Session() as db:
        event=db.get(Record,target); data=event.body(); data['delivery']='delivered'; event.set(data); db.commit()


async def run_job(job_id):
    with Session() as db:
        job=db.get(Job,job_id)
        kind,target=job.kind,job.target
    try:
        if kind=='document':
            await process_document(target)
        elif kind=='callback':
            await send_callback(target)
        else:
            raise ValueError('Unknown job type')
        with Session() as db:
            job=db.get(Job,job_id); job.state='done'; job.error=''; db.commit()
    except Exception as error:
        # Never log exception text: upstream URLs or document data may contain sensitive material.
        safe=str(error) if isinstance(error,ValueError) else type(error).__name__+'; inspect authorised service diagnostics'
        with Session() as db:
            job=db.get(Job,job_id)
            job.error=safe[:500]
            job.state='failed' if job.attempts>=3 else 'queued'
            job.available_at=now()+timedelta(seconds=20*job.attempts)
            if kind=='document':
                doc=db.get(Record,target)
                if doc and doc.body().get('state')!='processed':
                    data=doc.body(); data.update(state='failed' if job.state=='failed' else 'retrying',error=safe); doc.set(data)
            db.commit()
        log.warning('job_failure id=%s type=%s',job_id,type(error).__name__)


async def main():
    settings().validate_runtime()
    init_db()
    while True:
        job_id=claim()
        if job_id:
            await run_job(job_id)
        else:
            # SQL polling is the recovery path. Drain Service Bus notifications to avoid accumulation.
            if settings().azure_servicebus_namespace:
                try:
                    await asyncio.to_thread(drain_notifications)
                except Exception:
                    log.warning('queue_notification_unavailable')
            await asyncio.sleep(2)


def drain_notifications():
    from azure.servicebus import ServiceBusClient
    with ServiceBusClient(settings().azure_servicebus_namespace,credential()) as client:
        with client.get_queue_receiver(settings().azure_servicebus_queue,max_wait_time=1) as receiver:
            for msg in receiver.receive_messages(max_message_count=20,max_wait_time=1):
                receiver.complete_message(msg)


if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
