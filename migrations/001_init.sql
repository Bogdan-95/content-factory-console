
CREATE TYPE job_status AS ENUM ('queued', 'processing', 'done', 'failed');

CREATE TABLE jobs (
    id            BIGSERIAL PRIMARY KEY,
    prompt        TEXT        NOT NULL,
    negative      TEXT        NOT NULL DEFAULT '',
    width         INT         NOT NULL DEFAULT 1024,
    height        INT         NOT NULL DEFAULT 1024,
    steps         INT         NOT NULL DEFAULT 20,
    cfg           REAL        NOT NULL DEFAULT 7.0,
    seed          BIGINT      NOT NULL DEFAULT -1,
    status        job_status  NOT NULL DEFAULT 'queued',
    error         TEXT,
    comfy_prompt_id TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at    TIMESTAMPTZ,
    finished_at   TIMESTAMPTZ
);

CREATE INDEX idx_jobs_status_created ON jobs (status, created_at);

CREATE TABLE job_results (
    job_id     BIGINT PRIMARY KEY REFERENCES jobs (id) ON DELETE CASCADE,
    filename   TEXT     NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

