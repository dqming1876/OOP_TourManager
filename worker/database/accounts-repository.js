/** @implements {import('../ports.js').AccountsPort} */
export class AccountsRepository {
  constructor(db) {
    this.db = db;
  }

  findPublicById(id) {
    return this.db.prepare('SELECT id, username, name, email, phone, address, birthday FROM accounts WHERE id = ?')
      .bind(id).first();
  }

  findByUsername(username) {
    return this.db.prepare('SELECT * FROM accounts WHERE username = ?').bind(username).first();
  }

  async create({ id, username, name, hash, salt }) {
    const result = await this.db.prepare(`
      INSERT INTO accounts (id, username, name, password_hash, salt) VALUES (?, ?, ?, ?, ?)
      ON CONFLICT(username) DO NOTHING
    `).bind(id, username, name, hash, salt).run();
    return result.meta.changes === 1;
  }

  updateProfile(id, { name, email, phone, address, birthday }) {
    return this.db.prepare('UPDATE accounts SET name = ?, email = ?, phone = ?, address = ?, birthday = ? WHERE id = ?')
      .bind(name, email, phone, address, birthday, id).run();
  }
}
