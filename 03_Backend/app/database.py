import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, String, Text, Integer, DateTime, UniqueConstraint, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def uid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Record(Base):
    __tablename__ = 'records'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True, default='')
    data: Mapped[str] = mapped_column(Text, default='{}')
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    __mapper_args__ = {'version_id_col': version}

    def body(self):
        return json.loads(self.data)

    def set(self, value):
        self.data = json.dumps(value, ensure_ascii=False, allow_nan=False)

    def view(self):
        return dict(id=self.id, version=self.version, created_at=self.created_at.isoformat()+'Z', **self.body())


class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String(40))
    target: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(30), default='queued', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    error: Mapped[str] = mapped_column(Text, default='')


class Idempotency(Base):
    __tablename__ = 'idempotency'
    __table_args__ = (UniqueConstraint('principal', 'key', name='uq_idempotency'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    principal: Mapped[str] = mapped_column(String(200))
    key: Mapped[str] = mapped_column(String(200))
    digest: Mapped[str] = mapped_column(String(64))
    result_id: Mapped[str] = mapped_column(String(64))


if settings().database_url.startswith('sqlite:///'):
    Path(settings().database_url[10:]).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings().database_url, pool_pre_ping=True,
                       connect_args={'check_same_thread': False} if settings().database_url.startswith('sqlite') else {})
if engine.dialect.name == 'sqlite':
    @event.listens_for(engine, 'connect')
    def sqlite_options(connection, _):
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('PRAGMA busy_timeout=10000')
Session = sessionmaker(engine, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    with Session() as db:
        yield db


def add(db, kind, case_id, data):
    record = Record(kind=kind, case_id=case_id)
    record.set(data)
    db.add(record)
    db.flush()
    return record


def records(db, kind, case_id):
    return db.query(Record).filter_by(kind=kind, case_id=case_id).order_by(Record.created_at).all()


def audit(db, case_id, actor, action, detail=None):
    add(db, 'audit', case_id, {'actor': actor, 'action': action, 'detail': detail or {}})


def emit(db, case_id, event_type, payload=None):
    event_record = add(db, 'event', case_id, {'type':event_type, 'application_id':case_id,
                       'payload':payload or {}, 'delivery':'pending'})
    if settings().los_callback_url:
        db.add(Job(kind='callback', target=event_record.id))
    return event_record
