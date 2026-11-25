CREATE TABLE IF NOT EXISTS api_credentials (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    secret_value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_credentials_owner_user_id
ON api_credentials(owner_user_id);

CREATE INDEX IF NOT EXISTS idx_api_credentials_owner_provider
ON api_credentials(owner_user_id, provider);
