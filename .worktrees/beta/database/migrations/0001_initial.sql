-- Create initial tables if they do not exist
CREATE TABLE IF NOT EXISTS syllabus_uploads (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parsed_events (
    id UUID PRIMARY KEY,
    upload_id UUID REFERENCES syllabus_uploads(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    event_date DATE,
    event_type TEXT,
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
