import { accountsRoute } from './api/accounts-route.js';
import { errorResponse } from './api/http.js';
import { operationsRoute } from './api/operations-route.js';
import { AccountsRepository } from './database/accounts-repository.js';
import { BookingRepository } from './database/booking-repository.js';
import { ReportsRepository } from './database/reports-repository.js';
import { TourCatalogRepository } from './database/tour-catalog-repository.js';
import { AccessPolicy } from './service/access-policy.js';
import { AccountsService } from './service/accounts-service.js';
import { BookingService } from './service/booking-service.js';
import { ReportsService } from './service/reports-service.js';
import { authenticated } from './service/session.js';
import { TourCatalogService } from './service/tour-catalog-service.js';

const localDay = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' });
const d1Repositories = {
  accounts: db => db ? new AccountsRepository(db) : null,
  bookings: db => new BookingRepository(db),
  catalog: db => new TourCatalogRepository(db),
  reports: db => new ReportsRepository(db),
};

export function createWorker({ repositories = d1Repositories, today = () => localDay.format(new Date()) } = {}) {
  const attempts = new Map();

  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      try {
        if (url.pathname.startsWith('/api/')) {
          const settings = {
            ADMIN_USERNAME: env.ADMIN_USERNAME,
            ADMIN_PASSWORD_HASH: env.ADMIN_PASSWORD_HASH,
            ADMIN_PASSWORD_SALT: env.ADMIN_PASSWORD_SALT,
            ADMIN_SESSION_SECRET: env.ADMIN_SESSION_SECRET,
          };
          const accounts = new AccountsService(repositories.accounts(env.DB), settings, attempts);
          if (url.pathname.startsWith('/api/ops/')) {
            const access = new AccessPolicy(await accounts.currentAccount(request));
            const day = today();
            return await operationsRoute(request, url, {
              access,
              catalog: new TourCatalogService(repositories.catalog(env.DB), access, day),
              bookings: new BookingService(repositories.bookings(env.DB), access, day),
              reports: new ReportsService(repositories.reports(env.DB), access, day),
            });
          }
          return await accountsRoute(request, url.pathname, accounts, settings);
        }
        if (url.pathname === '/admin.js' && !await authenticated(request, env)) {
          return new Response('Unauthorized', { status: 401, headers: { 'Cache-Control': 'no-store' } });
        }
        if (!['GET', 'HEAD'].includes(request.method)) return new Response('Method not allowed', { status: 405 });
        const asset = await env.ASSETS.fetch(request);
        const response = new Response(asset.body, asset);
        response.headers.set('X-Content-Type-Options', 'nosniff');
        return response;
      } catch (error) {
        return errorResponse(error);
      }
    },
  };
}

export default createWorker();
