CREATE TABLE roles (
  name TEXT PRIMARY KEY CHECK(name IN ('admin','customer'))
);
INSERT INTO roles(name) VALUES ('admin'),('customer');
-- SQLite permits adding a REFERENCES column to populated tables only with a NULL default.
ALTER TABLE accounts ADD COLUMN role TEXT REFERENCES roles(name);
UPDATE accounts SET role = 'customer';
CREATE TRIGGER accounts_default_role AFTER INSERT ON accounts WHEN NEW.role IS NULL
BEGIN
  UPDATE accounts SET role = 'customer' WHERE id = NEW.id;
END;
-- The original application supports one administrator identity and its legacy signed cookie.
CREATE UNIQUE INDEX accounts_single_admin ON accounts(role) WHERE role = 'admin';
