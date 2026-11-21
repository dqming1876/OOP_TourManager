import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import worker from '../worker/index.js';
import { passwordHash } from '../worker/service/passwords.js';

export async function makeWorker({ adminPassword = randomUUID(), assets, seed } = {}) {
  const db = new DatabaseSync(':memory:', { enableForeignKeyConstraints: true });
  for (const migration of readdirSync('Database').filter(name => name.endsWith('.sql')).sort()) {
    db.exec(readFileSync('Database/' + migration, 'utf8'));
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
  const queries = [];
  const salt = randomUUID();
  const env = {
    ADMIN_USERNAME: 'demo_admin',
    ADMIN_PASSWORD_SALT: salt,
    ADMIN_PASSWORD_HASH: await passwordHash(adminPassword, salt),
    ADMIN_SESSION_SECRET: randomUUID(),
    ASSETS: assets,
    DB: {
      prepare(sql) {
        queries.push(sql);
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
  return { db, env, adminPassword, queries, fetch: request => worker.fetch(request, env) };
}
