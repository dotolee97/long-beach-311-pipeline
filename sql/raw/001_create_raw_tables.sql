CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.service_requests (
    payload      JSONB       NOT NULL,
    source_file  TEXT        NOT NULL,
    loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);