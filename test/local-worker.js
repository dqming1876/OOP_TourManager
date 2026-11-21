import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import worker from '../.cloudflare/worker.js';

export function makeWorker() {
  const db = new DatabaseSync(':memory:', { enableForeignKeyConstraints: true });
  for (const migration of readdirSync('drizzle').filter(name => name.endsWith('.sql')).sort()) {
    db.exec(readFileSync('drizzle/' + migration, 'utf8'));
  }
  const env = {
    ADMIN_USERNAME: 'demo_admin',
    ADMIN_PASSWORD: randomUUID(),
    ADMIN_SESSION_SECRET: randomUUID(),
    DB: {
      prepare(sql) {
        return { bind: (...args) => ({
          all: async () => ({ results: db.prepare(sql).all(...args) }),
          first: async () => db.prepare(sql).get(...args) || null,
          run: async () => ({ meta: db.prepare(sql).run(...args) }),
        }) };
      },
      async batch(statements) {
        db.exec('BEGIN');
        try {
          const results = await Promise.all(statements.map(statement => statement.all()));
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
