CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, username TEXT UNIQUE, role TEXT NOT NULL,
    password_salt TEXT, password_hash TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL, expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS areas (
    id TEXT PRIMARY KEY, ward_id TEXT NOT NULL, name TEXT NOT NULL,
    geometry_json TEXT NOT NULL, properties_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS road_nodes (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, longitude REAL NOT NULL, latitude REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS road_edges (
    id TEXT PRIMARY KEY, segment_id TEXT NOT NULL, source_node TEXT NOT NULL REFERENCES road_nodes(id),
    target_node TEXT NOT NULL REFERENCES road_nodes(id), name TEXT NOT NULL,
    length_m REAL NOT NULL, geometry_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY, source_key TEXT UNIQUE NOT NULL,
    source_id TEXT NOT NULL REFERENCES sources(id), area_id TEXT NOT NULL REFERENCES areas(id),
    variable TEXT NOT NULL, value REAL, unit TEXT NOT NULL, quality TEXT NOT NULL,
    observed_at TEXT NOT NULL, received_at TEXT NOT NULL, interval_minutes INTEGER NOT NULL,
    longitude REAL NOT NULL, latitude REAL NOT NULL, raw_fingerprint TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS observation_window ON observations(area_id, variable, observed_at, received_at);
CREATE TABLE IF NOT EXISTS quarantine (
    id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL,
    received_at TEXT NOT NULL, reason TEXT NOT NULL, raw_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS risk_runs (
    id TEXT PRIMARY KEY, area_id TEXT NOT NULL REFERENCES areas(id),
    fingerprint TEXT UNIQUE NOT NULL, issued_at TEXT NOT NULL, valid_until TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS risk_by_area ON risk_runs(area_id, issued_at);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY, area_id TEXT NOT NULL REFERENCES areas(id), onset TEXT,
    label_state TEXT NOT NULL, evidence_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
    area_id TEXT NOT NULL REFERENCES areas(id), description TEXT NOT NULL, severity TEXT NOT NULL,
    longitude REAL NOT NULL, latitude REAL NOT NULL, observed_at TEXT NOT NULL,
    submitted_at TEXT NOT NULL, expires_at TEXT NOT NULL, status TEXT NOT NULL,
    image_file TEXT, image_published INTEGER NOT NULL DEFAULT 0,
    review_reason TEXT, duplicate_of TEXT REFERENCES reports(id), deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS report_queue ON reports(status, observed_at);
CREATE TABLE IF NOT EXISTS hazards (
    id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports(id),
    edge_ids_json TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL, resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS active_hazards ON hazards(expires_at, resolved_at);
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
    ward_id TEXT NOT NULL, channel TEXT NOT NULL, consented_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1, UNIQUE(user_id, ward_id, channel)
);
CREATE TABLE IF NOT EXISTS alert_state (
    subscription_id TEXT PRIMARY KEY REFERENCES subscriptions(id),
    active_severity TEXT NOT NULL, last_notified_at TEXT, last_trigger TEXT
);
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
    subscription_id TEXT NOT NULL REFERENCES subscriptions(id), ward_id TEXT NOT NULL,
    kind TEXT NOT NULL, severity TEXT NOT NULL, trigger_id TEXT NOT NULL,
    idempotency_key TEXT UNIQUE NOT NULL, state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL,
    sent_at TEXT, message TEXT NOT NULL, support TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS alert_delivery ON alerts(state, next_attempt_at, expires_at);
CREATE TABLE IF NOT EXISTS audit (
    id TEXT PRIMARY KEY, actor_id TEXT, action TEXT NOT NULL, subject_id TEXT NOT NULL,
    at TEXT NOT NULL, detail_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
    status TEXT NOT NULL, details_json TEXT NOT NULL
);
