CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

ALTER TABLE workflows ADD COLUMN owner_user_id TEXT REFERENCES users(id);
