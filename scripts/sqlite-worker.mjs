import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import worker from '../.cloudflare/worker.js';

export function makeWorker({ adminPassword = randomUUID(), assets, seed } = {}) {
  const db = new DatabaseSync(':memory:', { enableForeignKeyConstraints: true });
  for (const migration of readdirSync('drizzle').filter(name => name.endsWith('.sql')).sort()) {
    db.exec(readFileSync('drizzle/' + migration, 'utf8'));
  }
  if (seed) {
    db.exec('BEGIN');
    try {
      db.exec(seed);
      db.exec('COMMIT');
    } catch (error) {
      db.exec('ROLLBACK');
      db.close();
      throw error;
    }
  }
  const env = {
    ADMIN_USERNAME: 'demo_admin',
    ADMIN_PASSWORD: adminPassword,
    ADMIN_SESSION_SECRET: randomUUID(),
    ASSETS: assets,
    DB: {
      prepare(sql) {
        const bind = (...args) => ({
          all: () => ({ results: db.prepare(sql).all(...args) }),
          first: () => db.prepare(sql).get(...args) || null,
          run: () => ({ meta: db.prepare(sql).run(...args) }),
        });
        return { bind, ...bind() };
      },
      batch(statements) {
        db.exec('BEGIN');
        try {
          const results = statements.map(statement => statement.all());
          db.exec('COMMIT');
          return results;
        } catch (error) {
          db.exec('ROLLBACK');
          throw error;
        }
      },
    },
  };
  return { db, env, fetch: request => worker.fetch(request, env) };
}
