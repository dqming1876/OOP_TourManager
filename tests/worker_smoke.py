"""Opt-in smoke test: python3 -m tests.worker_smoke (local Worker must be running)."""

def main():
    import json
    from urllib.request import Request,urlopen
    from urllib.error import HTTPError
    from uuid import uuid4
    from datetime import date,timedelta
    import os
    from getpass import getpass
    from urllib.parse import urlsplit
    BASE=os.environ.get('MINGO_SMOKE_ORIGIN', 'http://localhost:8787').rstrip('/')
    assert urlsplit(BASE).hostname in ('localhost', '127.0.0.1'), 'Smoke test only writes to localhost'
    admin_name=os.environ.get('MINGO_SMOKE_ADMIN', 'admin_local')
    admin_password=os.environ.get('MINGO_SMOKE_PASSWORD') or getpass('Local admin password: ')
    def call(path, body=None, cookie=None):
     headers={'Origin':BASE}
     if body is not None: headers['Content-Type']='application/json'
     if cookie: headers['Cookie']=cookie
     try:
      r=urlopen(Request(BASE+path, None if body is None else json.dumps(body).encode(), headers),timeout=30)
     except HTTPError as e:r=e
     raw=r.read(); data=json.loads(raw) if r.headers.get('Content-Type','').startswith('application/json') else None
     cookies='; '.join(h.split(';')[0] for h in r.headers.get_all('Set-Cookie',[]) if '=;' not in h)
     return r.status,data,cookies
    assert call('/')[0]==200
    status,data,_=call('/api/ops/tours');assert status==200,(status,data)
    status,data,admin=call('/api/auth/login',{'username':admin_name,'password':admin_password});assert status==200,(status,data)
    from tests.fixtures import TOUR
    status,data,_=call('/api/ops/tours',TOUR,admin);assert status==201,(status,data)
    tour=data['id']; day=(date.today()+timedelta(days=7)).isoformat()
    assert call(f'/api/ops/tours/{tour}/departures',{'day':day,'capacity':6},admin)[0]==200
    username='smoke_'+uuid4().hex[:12];password=uuid4().hex
    assert call('/api/auth/register',{'username':username,'password':password,'name':'Runtime smoke'})[0]==201
    status,data,guest=call('/api/auth/login',{'username':username,'password':password});assert status==200,(status,data)
    order={'tourId':tour,'day':day,'adults':1,'children':0,'name':'Runtime smoke','phone':'0900000000','expectedPrice':TOUR['price'],'requestId':uuid4().hex}
    first=call('/api/ops/bookings',order,guest);assert first[0]==201,first[:2]
    second=call('/api/ops/bookings',order,guest);assert second[:2]==first[:2]
    assert call('/api/ops/bookings',{**order,'requestId':uuid4().hex,'expectedPrice':1},guest)[0]==409
    for action in ('confirm','collect','refund','cancel'):
        assert call('/api/ops/bookings/'+first[1]['id']+'/'+action,{},admin)[0]==200
    assert call('/api/ops/destinations')[0]==200
    assert call('/api/ops/reports',cookie=admin)[0]==200
    print('PASS: actual Python Worker + local D1: assets, catalog, admin login, create tour/departure, register/login, booking retry, stale quote, cancel, reports.')


if __name__ == "__main__":
    main()
