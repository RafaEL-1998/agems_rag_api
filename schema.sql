CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    sector TEXT NOT NULL,
    source_url TEXT,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    r2_key TEXT NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending'
);

CREATE INDEX idx_documents_sector ON documents(sector);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_status ON documents(status);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    context_chunks TEXT,
    model_used TEXT,
    tokens_used INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_session ON conversations(session_id, timestamp);
CREATE INDEX idx_conversations_user ON conversations(user_id, timestamp);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active'
);

CREATE INDEX idx_sessions_user ON sessions(user_id, last_activity);

