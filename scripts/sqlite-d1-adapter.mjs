// Object adapter for the subset of the Worker D1 API used by repositories.
export class SqliteD1Adapter {
  constructor(database, queries) {
    this.database = database;
    this.queries = queries;
  }

  prepare(sql) {
    this.queries.push(sql);
    const bind = (...args) => ({
      all: () => ({ results: this.database.prepare(sql).all(...args) }),
      first: () => this.database.prepare(sql).get(...args) || null,
      run: () => ({ meta: this.database.prepare(sql).run(...args) }),
    });
    return { bind, ...bind() };
  }

  batch(statements) {
    this.database.exec('BEGIN');
    try {
      const results = statements.map(statement => statement.all());
      this.database.exec('COMMIT');
      return results;
    } catch (error) {
      this.database.exec('ROLLBACK');
      throw error;
    }
  }
}
