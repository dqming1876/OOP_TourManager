-- Shared across Worker isolates. No plaintext IP addresses are stored.
CREATE TABLE login_attempts (
    key TEXT PRIMARY KEY,
    count INTEGER NOT NULL CHECK (count BETWEEN 1 AND 12),
    expires_at INTEGER NOT NULL
);
CREATE INDEX login_attempts_expiry ON login_attempts(expires_at);
