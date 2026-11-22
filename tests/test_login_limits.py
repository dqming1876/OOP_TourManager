from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
from backend.app import Application
from tests.fixtures import api, last_seats


class SharedLoginLimits(IsolatedAsyncioTestCase):
    def setUp(self):
        self.worker = last_seats()
        self.addCleanup(self.worker.database.close)
        self.db = self.worker.database

    async def test_login_limit_shared_across_app_instances_and_expires(self):
        body = {'username': 'demo_admin', 'password': 'wrong-test-password'}
        with patch('backend.services.time', return_value=1000):
            for _ in range(12):
                self.worker.app = Application()
                self.assertEqual((await api(self.worker, '/api/auth/login', body)).status, 401)
            self.worker.app = Application()
            self.assertEqual((await api(self.worker, '/api/auth/login', body)).status, 429)
        with patch('backend.services.time', return_value=1299):
            self.assertEqual((await api(self.worker, '/api/auth/login', body)).status, 429)
        with patch('backend.services.time', return_value=1300):
            self.assertEqual((await api(self.worker, '/api/auth/login', body)).status, 401)

    async def test_successful_login_clears_attempt_window(self):
        with patch('backend.services.time', return_value=1000):
            for _ in range(11):
                await api(self.worker, '/api/auth/login', {'username': 'demo_admin', 'password': 'wrong'})
            response = await api(self.worker, '/api/auth/login', {'username': 'demo_admin', 'password': self.worker.admin_password})
            self.assertEqual(response.status, 200)
            self.assertEqual(self.db.execute('SELECT count(*) FROM login_attempts').fetchone()[0], 0)
