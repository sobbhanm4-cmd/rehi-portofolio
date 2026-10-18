import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient

os.environ['ADMIN_PASSWORD'] = 'test-password-long-enough-12345678'
from app import app
from db import Base, engine

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///'+str(tmp_path/'test.db'))
    engine.cache_clear()
    Base.metadata.create_all(engine())
    with TestClient(app) as c:
        yield c
    engine().dispose()
    engine.cache_clear()

AUTH = {'x-admin-password': os.environ['ADMIN_PASSWORD']}
DAY = (datetime.now(ZoneInfo('Asia/Dubai'))+timedelta(days=2)).date().isoformat()

def payload(**changes):
    p = dict(request_id=str(uuid.uuid4()), date=DAY, time='12:00', name='Test Founder', email='founder@example.com', whatsapp='+44 7700 900000', role='Founder', content_status='Actively creating content', budget='$2,500 – $5,000 / month', consent=True)
    return p | changes

def open_day(c):
    assert c.put('/api/admin-availability', headers=AUTH, json={'date':DAY, 'times':['12:00','12:30']}).status_code == 200

def test_full_lifecycle(client):
    c=client
    assert c.get('/api/admin-bookings').status_code == 401
    assert c.get('/api/availability',params={'date':DAY}).json()['available'] == []
    open_day(c)
    assert c.get('/api/availability',params={'date':DAY}).json()['timezone'] == 'Asia/Dubai'
    p=payload()
    r=c.post('/api/book',json=p)
    assert r.status_code == 201
    id=r.json()['id']
    assert c.post('/api/book',json=p).json()['id'] == id
    assert c.post('/api/book',json=payload()).status_code == 409
    assert c.get('/api/availability',params={'date':DAY}).json()['available'] == ['12:30']
    b=c.get('/api/admin-bookings',headers=AUTH).json()['bookings'][0]
    assert b['start'].endswith('+04:00')
    assert (b['role'], b['content_status'],b['budget']) == (p['role'],p['content_status'],p['budget'])
    assert c.patch('/api/admin-bookings/'+id,headers=AUTH,json={'status':'confirmed','meetLink':'https://meet.google.com/abc-defg-hij'}).status_code==200
    assert c.patch('/api/admin-bookings/'+id,headers=AUTH,json={'status':'cancelled'}).status_code==200
    assert c.post('/api/book',json=payload()).status_code==201
    assert c.patch('/api/admin-bookings/'+id,headers=AUTH,json={'status':'confirmed'}).status_code==409

def test_simultaneous_bookings(client):
    open_day(client)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda p:client.post('/api/book',json=p).status_code,[payload(),payload()]))
    assert sorted(results)==[201,409]

def test_validation_and_privacy(client):
    open_day(client)
    for changes in [{'budget':'invalid'},{'role':'Unknown'},{'consent':False},{'email':'bad'},{'whatsapp':'123'},{'time':'12:15'},{'date':'2026-02-30'},{'website':'bot'}]:
        assert client.post('/api/book',json=payload(**changes)).status_code==422
    assert client.post('/api/book',json=payload(time='13:00')).status_code==409
    assert client.put('/api/admin-availability',headers=AUTH,json={'date':DAY,'times':['12:15']}).status_code==422
    assert client.get('/api/admin-bookings',headers=AUTH).headers['cache-control']=='no-store'
    for path in ['/app.py','/.env','/local-bookings.db','/db.py']:
        assert client.get(path).status_code==404

def test_auth_throttle(client):
    for _ in range(10):
        assert client.get('/api/admin-bookings').status_code==401
    assert client.get('/api/admin-bookings').status_code==429
    assert client.get('/api/admin-bookings',headers=AUTH).status_code==200

def test_booking_throttle(client):
    open_day(client)
    for _ in range(12):
        client.post('/api/book',json=payload(time='13:00'))
    assert client.post('/api/book',json=payload()).status_code==429
