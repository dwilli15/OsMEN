-- Create OsMEN application database and user
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'osmen_app') THEN
      CREATE ROLE osmen_app LOGIN PASSWORD 'osmen_app_password';
   END IF;
END
$$;

DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'osmen_app') THEN
      CREATE DATABASE osmen_app OWNER osmen_app;
   END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE osmen_app TO osmen_app;

\c osmen_app

CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION osmen_app;
SET search_path TO app, public;

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

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
