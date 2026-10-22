"""Synthetic LOS event receiver. HMAC, replay window, durable deduplication."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import time
from fastapi import FastAPI, Request, HTTPException

app=FastAPI(title='VCA LOS Simulator',version='0.1.0')
DB=os.getenv('LOS_DATABASE','./data/los.db')
SECRET=os.getenv('LOS_CALLBACK_SECRET','')


def connection():
    Path(DB).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, received INTEGER, payload TEXT)')
    return db


@app.get('/health')
def health():
    return {'status':'ok','purpose':'Synthetic LOS simulator; not a real LOS connection'}


@app.post('/events')
async def event(request:Request):
    if len(SECRET)<24:
        raise HTTPException(503,'Callback secret not configured')
    raw=await request.body()
    if len(raw)>1024*1024:
        raise HTTPException(413,'Event too large')
    timestamp=request.headers.get('X-VCA-Timestamp','')
    try:
        if abs(time.time()-int(timestamp))>300:
            raise ValueError()
    except ValueError:
        raise HTTPException(401,'Expired or invalid timestamp')
    expected=hmac.new(SECRET.encode(),timestamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,request.headers.get('X-VCA-Signature','')):
        raise HTTPException(401,'Invalid signature')
    body=json.loads(raw)
    event_id=request.headers.get('X-VCA-Event-ID','')
    if not event_id or body.get('id')!=event_id:
        raise HTTPException(400,'Event identifier mismatch')
    with connection() as db:
        previous=db.execute('SELECT payload FROM events WHERE id=?',(event_id,)).fetchone()
        if previous and json.loads(previous[0])!=body:
            raise HTTPException(409,'Event identifier reused with changed payload')
        db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?)',(event_id,int(time.time()),raw.decode()))
    return {'accepted':True,'event_id':event_id,'duplicate':bool(previous)}


@app.get('/events')
def events(request:Request):
    supplied=request.headers.get('Authorization','').removeprefix('Bearer ')
    if len(SECRET)<24 or not hmac.compare_digest(supplied,SECRET):
        raise HTTPException(401,'Simulator inspection token required')
    with connection() as db:
        return [json.loads(row[0]) for row in db.execute('SELECT payload FROM events ORDER BY received DESC LIMIT 100')]
