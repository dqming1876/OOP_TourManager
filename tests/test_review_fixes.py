import asyncio
import json
from unittest import IsolatedAsyncioTestCase

from tests.fixtures import GUEST, ORDER, api, cookie, last_seats


class ReviewFixes(IsolatedAsyncioTestCase):
    def setUp(self):
        self.worker = last_seats()
        self.addCleanup(self.worker.database.close)
        self.db = self.worker.database
        self.token = cookie(self.worker, GUEST)
        self.order = {**ORDER, "requestId": "retry-test"}

    async def place(self, **changes):
        return await api(self.worker, '/api/ops/bookings', {**self.order, **changes}, self.token)

    async def test_retry_with_full_departure_reserves_once(self):
        results = await asyncio.gather(self.place(), self.place())
        self.assertEqual([r.status for r in results], [201, 201])
        self.assertEqual(results[0].body, results[1].body)
        self.assertEqual(self.db.execute('SELECT count(*) FROM bookings').fetchone()[0], 1)
        self.assertEqual(self.db.execute("SELECT reserved FROM departures WHERE tour_id='axis5-tour'").fetchone()[0], 3)

    async def test_retry_does_not_recreate_cancelled_order(self):
        first = await self.place()
        order_id = json.loads(first.body)['id']
        self.db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (order_id,))
        self.assertEqual((await self.place()).body, first.body)
        self.assertEqual(self.db.execute("SELECT reserved FROM departures WHERE tour_id='axis5-tour'").fetchone()[0], 0)

    async def test_reusing_key_with_changed_details_is_rejected(self):
        await self.place()
        self.assertEqual((await self.place(name='Different guest')).status, 409)

    async def test_new_intent_can_create_new_booking(self):
        self.db.execute("UPDATE departures SET capacity=9 WHERE tour_id='axis5-tour'")
        first, second = await self.place(), await self.place(requestId='new-intent')
        self.assertEqual((first.status, second.status), (201, 201))
        self.assertNotEqual(first.body, second.body)

    async def test_stale_price_rejected_without_reserving_seats(self):
        self.db.execute("UPDATE tours SET price=600000 WHERE id='axis5-tour'")
        response = await self.place()
        self.assertEqual((response.status, json.loads(response.body)['field']), (409, 'expectedPrice'))
        self.assertEqual(self.db.execute('SELECT count(*) FROM bookings').fetchone()[0], 0)
        self.assertEqual((await self.place(expectedPrice=600000)).status, 201)

    async def test_missing_booking_contract_is_rejected(self):
        for field in ('requestId', 'expectedPrice'):
            self.assertEqual((await self.place(**{field: None})).status, 400)

