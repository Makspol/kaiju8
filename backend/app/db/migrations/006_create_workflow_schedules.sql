CREATE TABLE IF NOT EXISTS workflow_schedules (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,
    trigger_node_id TEXT NOT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    schedule_json TEXT NOT NULL,
    next_run_at TEXT,
    last_run_at TEXT,
    last_execution_id TEXT,
    last_error TEXT,
    locked_until TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (workflow_id, trigger_node_id),
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (last_execution_id) REFERENCES executions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_workflow_schedules_due
ON workflow_schedules(status, next_run_at, locked_until);

CREATE INDEX IF NOT EXISTS idx_workflow_schedules_owner
ON workflow_schedules(owner_user_id);
