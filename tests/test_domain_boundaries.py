"""Regression coverage for the independent review, including direct service calls."""
import ast
import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock

from backend.domain import AppError, Booking, BookingStatus, PaymentKind, Role
from backend.repositories import ReportsRepository
from backend.services import AccessPolicy, BookingService, TourCatalogService
from scripts.sqlite_worker import ROOT
from tests.fixtures import ADMIN, GUEST, ORDER, TODAY, TOUR, api, cookie, last_seats


class ServiceAuthorization(IsolatedAsyncioTestCase):
    async def test_admin_guards_before_repository(self):
        methods = ['save_tour', 'set_visibility', 'remove_departure', 'payment_history']
        for access, status in [(GUEST, 403), (AccessPolicy(None), 401)]:
            for method in methods:
                with self.subTest(method=method, status=status):
                    port = SimpleNamespace(**{name: AsyncMock(return_value=True) for name in methods})
                    catalog = TourCatalogService(port, access, TODAY)
                    bookings = BookingService(port, access, TODAY)
                    args = {'save_tour': (None, TOUR), 'set_visibility': ('t', True),
                            'remove_departure': ('t', TODAY), 'payment_history': ('b',)}
                    service = bookings if method == 'payment_history' else catalog
                    with self.assertRaises(AppError) as error:
                        await getattr(service, method)(*args[method])
                    self.assertEqual(error.exception.status, status)
                    for name in methods:
                        getattr(port, name).assert_not_called()


class DomainInvariants(TestCase):
    def test_pending_and_cancelled_cannot_be_paid(self):
        booking = Booking.request('b', 'u', ORDER)
        for status in (BookingStatus.PENDING, BookingStatus.CANCELLED):
            with self.subTest(status=status), self.assertRaises(AppError):
                replace(booking, status=status, paid=True)
        self.assertTrue(replace(booking, status=BookingStatus.CONFIRMED, paid=True).paid)
        self.assertIs(booking.status, BookingStatus.PENDING)
        self.assertEqual(json.loads(json.dumps([Role.ADMIN, PaymentKind.REFUND])), ['admin', 'refund'])

    def test_services_do_not_read_http_headers_or_cookies(self):
        for filename in ('services.py', 'login_limits.py', 'destinations.py'):
            tree = ast.parse((ROOT / 'backend' / filename).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, ('header', 'headers', 'cookies'))


class ReviewBoundaries(IsolatedAsyncioTestCase):
    def setUp(self):
        self.worker = last_seats()
        self.addCleanup(self.worker.database.close)
        self.db = self.worker.database
        self.admin = cookie(self.worker)
        self.guest = cookie(self.worker, GUEST)

    async def test_capacity_can_equal_reserved_but_not_below(self):
        self.assertEqual((await api(self.worker, '/api/ops/bookings', ORDER, self.guest)).status, 201)
        path = '/api/ops/tours/axis5-tour/departures'
        self.assertEqual((await api(self.worker, path, {'day': ORDER['day'], 'capacity': 3, 'edit': True}, self.admin)).status, 200)
        self.assertEqual((await api(self.worker, path, {'day': ORDER['day'], 'capacity': 2, 'edit': True}, self.admin)).status, 409)
        self.assertEqual(tuple(self.db.execute("SELECT capacity,reserved FROM departures WHERE tour_id='axis5-tour'").fetchone()), (3, 3))

    async def test_pending_today_not_expired_and_paid_today_not_completed(self):
        response = await api(self.worker, '/api/ops/bookings', ORDER, self.guest)
        booking = json.loads(response.body)['id']
        repo = ReportsRepository(self.worker.db)
        day = ORDER['day']
        async def states(today):
            result = await repo.load('0001-01-01', '9999-12-31', '', today)
            return {row['state'] for row in result['bookings']}
        self.assertEqual(await states(day), {'pending'})
        self.assertEqual(await states('2028-03-08'), {'expired'})
        self.db.execute("UPDATE bookings SET status='confirmed',paid=1 WHERE id=?", (booking,))
        self.assertEqual(await states(day), {'confirmed'})
        self.assertEqual(await states('2028-03-08'), {'completed'})

    async def test_registration_password_five_rejected_six_accepted(self):
        body = {'name': 'Khách kiểm thử', 'username': 'boundary_guest', 'password': '12345'}
        self.assertEqual((await api(self.worker, '/api/auth/register', body)).status, 400)
        self.assertEqual((await api(self.worker, '/api/auth/register', {**body, 'password': '123456'})).status, 201)

    async def test_admin_is_persisted_and_database_hash_is_authoritative(self):
        credentials = {'username': self.worker.settings.username, 'password': self.worker.admin_password}
        self.assertEqual((await api(self.worker, '/api/auth/login', credentials)).status, 200)
        row = self.db.execute("SELECT role,password_hash FROM accounts WHERE id='admin'").fetchone()
        self.assertEqual(row['role'], 'admin')
        self.assertNotEqual(row['password_hash'], credentials['password'])
        self.db.execute("UPDATE accounts SET password_hash='changed' WHERE id='admin'")
        self.assertEqual((await api(self.worker, '/api/auth/login', credentials)).status, 401)
        self.db.execute("UPDATE accounts SET role='customer' WHERE id='admin'")
        result = await api(self.worker, '/api/admin/session', token=self.admin)
        self.assertFalse(json.loads(result.body)['authenticated'])

    async def test_destinations_shared_and_stale_write_rejected(self):
        path = '/api/ops/destinations'
        result = await api(self.worker, path)
        entries = json.loads(result.body)['entries']
        self.assertEqual(len(entries), 204)
        original = entries[0]
        body = {**original, 'description': 'Mô tả đã cập nhật', 'url': 'https://example.com/image.jpg'}
        target = path + '/' + original['id']
        self.assertEqual((await api(self.worker, target, body, self.guest)).status, 403)
        self.assertEqual((await api(self.worker, target, body, self.admin)).status, 200)
        self.assertEqual((await api(self.worker, target, body, self.admin)).status, 409)
        public = json.loads((await api(self.worker, path)).body)['entries'][0]
        self.assertEqual(public['description'], body['description'])
        self.assertEqual(public['version'], original['version'] + 1)
        self.assertEqual((await api(self.worker, target, {**public, 'url': 'javascript:alert(1)'}, self.admin)).status, 400)
        self.assertEqual((await api(self.worker, target, {**public, 'url': 'http://127.0.0.1:4173/images/demo.jpg'}, self.admin)).status, 400)
        self.assertEqual((await api(self.worker, target, {**public, 'url': '/images/../secret.jpg'}, self.admin)).status, 400)
        self.assertEqual((await api(self.worker, target, {**public, 'url': '/images/fill-north-6b2f8e99a0.jpg'}, self.admin)).status, 200)
        reloaded = json.loads((await api(self.worker, path)).body)['entries'][0]
        self.assertEqual((await api(self.worker, target + '/remove', {'version': reloaded['version']}, self.admin)).status, 200)

    async def test_destinations_duplicate_and_last_item_guard(self):
        path = '/api/ops/destinations'
        entries = json.loads((await api(self.worker, path)).body)['entries']
        first = entries[0]
        body = {**first, 'description': 'Kiểm thử', 'url': 'https://example.com/a.jpg'}
        self.assertEqual((await api(self.worker, path, body, self.admin)).status, 409)
        body['name'] = 'Điểm thử mới'
        self.assertEqual((await api(self.worker, path, body, self.admin)).status, 200)
        group = [e for e in json.loads((await api(self.worker, path)).body)['entries']
                 if e['province_id'] == first['province_id'] and e['kind'] == first['kind']]
        for item in group[:-1]:
            self.assertEqual((await api(self.worker, path+'/'+item['id']+'/remove', {'version': 1}, self.admin)).status, 200)
        self.assertEqual((await api(self.worker, path+'/'+group[-1]['id']+'/remove', {'version': 1}, self.admin)).status, 409)


class SchemaUpgrade(TestCase):
    def test_old_tour_content_preserved_and_extracted(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.execute('PRAGMA foreign_keys=ON')
        migrations = sorted((ROOT / 'Database').glob('*.sql'))
        for migration in migrations:
            if migration.name >= '0007':
                break
            db.executescript(migration.read_text())
        db.execute("INSERT INTO accounts(id,username,name,password_hash,salt) VALUES ('old','old_user','Khách cũ','hash','salt')")
        before = db.execute('SELECT id,content FROM tours').fetchall()
        for migration in migrations:
            if migration.name >= '0007':
                db.executescript(migration.read_text())
        self.assertEqual(db.execute('SELECT id,content FROM legacy_tour_content').fetchall(), before)
        for tour_id, content in before:
            data = json.loads(content)
            self.assertEqual(db.execute('SELECT title,province,place,days,"desc" FROM tours WHERE id=?', (tour_id,)).fetchone(),
                             tuple(data.get(key, 1 if key == 'days' else '') for key in ('title','province','place','days','desc')))
        self.assertNotIn('content', [row[1] for row in db.execute('PRAGMA table_info(tours)')])
        self.assertEqual(db.execute("SELECT role FROM accounts WHERE id='old'").fetchone()[0], 'customer')
        self.assertFalse(db.execute('PRAGMA foreign_key_check').fetchall())
