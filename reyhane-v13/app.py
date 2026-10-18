import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import date as Date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from db import Day, Booking, RateLimit, session

app = FastAPI(title='RN Studio Booking', docs_url=None, redoc_url=None, openapi_url=None)
ZONE = ZoneInfo('Asia/Dubai')
TIMES = [f'{h:02}:{m:02}' for h in range(24) for m in (0, 30)]
ROLES = Literal['Founder', 'Podcaster', 'Content Creator', 'Other']
CONTENT = Literal['Actively creating content', 'Brand is active, content is inconsistent', 'Not started yet']
BUDGET = Literal['Under $2,500 / month', '$2,500 – $5,000 / month', '$5,000 – $10,000 / month', '$10,000 – $20,000 / month', '$20,000+ / month']

@app.middleware('http')
async def headers(request: Request, call_next):
    if request.url.path.startswith('/api/'):
        if len(await request.body()) > 16000:
            return JSONResponse({'error': 'Request is too large.'}, status_code=413)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.exception_handler(HTTPException)
async def http_error(request, error):
    return JSONResponse({'error': error.detail}, status_code=error.status_code)

@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    return JSONResponse({'error': 'Please check the required fields, email, and selected answers.'}, status_code=422)

@app.exception_handler(SQLAlchemyError)
async def database_error(request, error):
    return JSONResponse({'error': 'Booking service is temporarily unavailable. Please try again.'}, status_code=503)

def day_key(value):
    try:
        d = Date.fromisoformat(value)
        if d.isoformat() != value:
            raise ValueError()
        return d
    except (ValueError, TypeError):
        raise HTTPException(422, 'Choose a valid date.')

def stamp(day, clock):
    return datetime.fromisoformat(f'{day}T{clock}').replace(tzinfo=ZONE)

def in_window(day, clock):
    now = datetime.now(ZONE)
    return clock in TIMES and now + timedelta(hours=1) < stamp(day, clock) < now + timedelta(days=90)

def rate_limit(request, scope, limit, seconds):
    # Vercel sets this header at its trusted edge. Local requests use socket IP.
    ip = request.headers.get('x-vercel-forwarded-for', '') if os.getenv('VERCEL') else ''
    ip = ip.split(',')[0].strip() or (request.client.host if request.client else 'unknown')
    digest = hmac.new(os.getenv('ADMIN_PASSWORD', '').encode(), ip.encode(), hashlib.sha256).hexdigest()
    now = int(time.time())
    key = f'{scope}:{digest}:{now // seconds}'
    with session() as s:
        dialect = s.bind.dialect.name
        if dialect == 'postgresql':
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        stmt = insert(RateLimit).values(key=key, count=1, expires=now+seconds*2)
        stmt = stmt.on_conflict_do_update(index_elements=['key'], set_={'count': RateLimit.count+1}).returning(RateLimit.count)
        count = s.execute(stmt).scalar_one()
        s.execute(delete(RateLimit).where(RateLimit.expires < now))
        s.commit()
    if count > limit:
        raise HTTPException(429, 'Too many attempts. Please try again later.')

def admin(request: Request):
    expected = os.getenv('ADMIN_PASSWORD', '')
    if len(expected) < 24:
        raise HTTPException(503, 'Set an admin password of at least 24 characters on the server.')
    actual = request.headers.get('x-admin-password', '')
    if not hmac.compare_digest(actual.encode(), expected.encode()):
        rate_limit(request, 'admin', 10, 900)
        raise HTTPException(401, 'Incorrect admin password.')

class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

class Reservation(Input):
    request_id: uuid.UUID
    date: str
    time: str
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=254)
    whatsapp: str = Field(pattern=r'^\+[1-9][0-9 ()-]{6,23}$', max_length=25)
    role: ROLES
    content_status: CONTENT
    budget: BUDGET
    note: str = Field(default='', max_length=1500)
    website: str = Field(default='', max_length=300)
    consent: Literal[True]

class Availability(Input):
    date: str
    times: list[str] = Field(max_length=48)
    @field_validator('times')
    @classmethod
    def valid_times(cls, value):
        if any(t not in TIMES for t in value):
            raise ValueError('Invalid time')
        return sorted(set(value))

class BookingUpdate(Input):
    status: Literal['requested', 'confirmed', 'completed', 'cancelled']
    meetLink: str = Field(default='', max_length=500)
    @field_validator('meetLink')
    @classmethod
    def valid_meet(cls, value):
        if value:
            u = urlparse(value)
            if u.scheme != 'https' or u.hostname != 'meet.google.com' or u.username or u.password:
                raise ValueError('Use a Google Meet HTTPS link')
        return value

@app.get('/api/availability')
def availability(date: str):
    day_key(date)
    with session() as s:
        day = s.get(Day, date)
        allowed = json.loads(day.times) if day else []
        busy = set(s.scalars(select(Booking.time).where(Booking.date == date, Booking.active_slot.is_not(None))))
    return {'available': [t for t in allowed if t not in busy and in_window(date, t)], 'timezone': 'Asia/Dubai'}

@app.post('/api/book', status_code=201)
def book(data: Reservation, request: Request):
    day_key(data.date)
    if data.website:
        raise HTTPException(422, 'Unable to submit this request.')
    if not in_window(data.date, data.time):
        raise HTTPException(422, 'Select a time at least one hour ahead and within 90 days.')
    rate_limit(request, 'booking', 12, 3600)
    with session() as s:
        existing = s.scalar(select(Booking).where(Booking.request_id == str(data.request_id)))
        if existing:
            return {'id': existing.id, 'status': existing.status}
        # Serialize edits of this day's availability with new bookings on PostgreSQL.
        day = s.scalar(select(Day).where(Day.date == data.date).with_for_update())
        if not day or data.time not in json.loads(day.times):
            raise HTTPException(409, 'This time is no longer available. Please choose another.')
        values = data.model_dump(exclude={'request_id', 'website', 'consent'})
        b = Booking(**values, id=str(uuid.uuid4()), request_id=str(data.request_id), active_slot=f'{data.date} {data.time}')
        s.add(b)
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            existing = s.scalar(select(Booking).where(Booking.request_id == str(data.request_id)))
            if existing:
                return {'id': existing.id, 'status': existing.status}
            raise HTTPException(409, 'This time was just booked. Please choose another.')
        return {'id': b.id, 'status': b.status}

@app.get('/api/admin-availability', dependencies=[Depends(admin)])
def admin_day(date: str):
    day_key(date)
    with session() as s:
        day = s.get(Day, date)
        return {'times': json.loads(day.times) if day else []}

@app.put('/api/admin-availability', dependencies=[Depends(admin)])
def save_day(data: Availability):
    d = day_key(data.date)
    if not datetime.now(ZONE).date() <= d <= (datetime.now(ZONE)+timedelta(days=90)).date():
        raise HTTPException(422, 'Choose a date within the next 90 days.')
    with session() as s:
        if s.bind.dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        stmt = insert(Day).values(date=data.date, times=json.dumps(data.times))
        s.execute(stmt.on_conflict_do_update(index_elements=['date'], set_={'times': json.dumps(data.times)}))
        s.commit()
    return {'saved': True}

def serialize(b):
    return {'id': b.id, 'start': stamp(b.date, b.time).isoformat(), 'name': b.name, 'email': b.email,
            'whatsapp': b.whatsapp, 'role': b.role, 'content_status': b.content_status,
            'budget': b.budget, 'note': b.note, 'status': b.status, 'meetLink': b.meet_link,
            'createdAt': b.created_at.isoformat()}

@app.get('/api/admin-bookings', dependencies=[Depends(admin)])
def bookings():
    with session() as s:
        return {'bookings': [serialize(b) for b in s.scalars(select(Booking).order_by(Booking.date.desc(), Booking.time.desc()))]}

@app.patch('/api/admin-bookings/{booking_id}', dependencies=[Depends(admin)])
def update_booking(booking_id: uuid.UUID, data: BookingUpdate):
    with session() as s:
        b = s.scalar(select(Booking).where(Booking.id == str(booking_id)).with_for_update())
        if not b:
            raise HTTPException(404, 'Booking not found.')
        if b.status == 'cancelled' and data.status != 'cancelled':
            raise HTTPException(409, 'Cancelled bookings cannot be reopened. Create a new booking.')
        b.status = data.status
        b.meet_link = data.meetLink
        if data.status == 'cancelled':
            b.active_slot = None
        s.commit()
        return {'booking': serialize(b)}

@app.get('/api/health')
def health():
    return {'ok': True}

@app.get('/admin', include_in_schema=False)
def admin_page():
    return RedirectResponse('/admin.html')

# Vercel serves public/ directly. Only local development mounts the directory.
if not os.getenv('VERCEL'):
    app.mount('/', StaticFiles(directory=Path(__file__).parent/'public', html=True), name='public')
