"""Persistent PostgreSQL in production; SQLite is for local development only."""
import os
from functools import lru_cache
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool

class Base(DeclarativeBase):
    pass

class Day(Base):
    __tablename__ = 'availability'
    date: Mapped[str] = mapped_column(String(10), primary_key=True)
    times: Mapped[str] = mapped_column(Text, default='[]')

class Booking(Base):
    __tablename__ = 'bookings'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), unique=True)
    active_slot: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    date: Mapped[str] = mapped_column(String(10), index=True)
    time: Mapped[str] = mapped_column(String(5))
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254))
    whatsapp: Mapped[str] = mapped_column(String(25))
    role: Mapped[str] = mapped_column(String(30))
    content_status: Mapped[str] = mapped_column(String(50))
    budget: Mapped[str] = mapped_column(String(50))
    note: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='requested')
    meet_link: Mapped[str] = mapped_column(String(500), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class RateLimit(Base):
    __tablename__ = 'rate_limits'
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    expires: Mapped[int] = mapped_column(Integer)

@lru_cache
def engine():
    url = os.getenv('DATABASE_URL', '')
    if os.getenv('VERCEL') and not url.startswith(('postgres://', 'postgresql://', 'postgresql+psycopg://')):
        raise RuntimeError('Set a persistent PostgreSQL DATABASE_URL in Vercel.')
    url = url or 'sqlite:///./local-bookings.db'
    if url.startswith(('postgres://', 'postgresql://')):
        url = 'postgresql+psycopg://' + url.split('://', 1)[1]
    options = {'pool_pre_ping': True}
    if url.startswith('postgresql'):
        options['poolclass'] = NullPool
        options['connect_args'] = {'connect_timeout': 10}
    else:
        options['connect_args'] = {'check_same_thread': False, 'timeout': 15}
    return create_engine(url, **options)

def session():
    return sessionmaker(bind=engine(), expire_on_commit=False)()

