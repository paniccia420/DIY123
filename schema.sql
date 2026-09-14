-- DIY Help App — Content Pipeline Schema
-- Postgres 14+ (uses pgvector extension for semantic search)

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------- Categories ----------

CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL UNIQUE,
    slug        TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE subcategories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL,
    UNIQUE (category_id, slug)
);

-- ---------- Sources ----------

CREATE TABLE sources (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type        TEXT NOT NULL CHECK (type IN ('youtube', 'blog', 'forum')),
    domain      TEXT NOT NULL,
    trust_score NUMERIC(3,2) DEFAULT 0.50
);

-- ---------- Tutorials ----------

CREATE TABLE tutorials (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID NOT NULL REFERENCES sources(id),
    category_id     UUID NOT NULL REFERENCES categories(id),
    subcategory_id  UUID REFERENCES subcategories(id),
    title           TEXT NOT NULL,
    url             TEXT NOT NULL UNIQUE,
    content_type    TEXT NOT NULL CHECK (content_type IN ('video', 'article', 'thread')),
    summary         TEXT,
    raw_text        TEXT,
    duration_seconds INTEGER,
    difficulty      TEXT CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    embedding       VECTOR(1536),
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active       BOOLEAN NOT NULL DEFAULT true
);

CREATE INDEX idx_tutorials_category ON tutorials(category_id);
CREATE INDEX idx_tutorials_subcategory ON tutorials(subcategory_id);
CREATE INDEX idx_tutorials_embedding ON tutorials USING ivfflat (embedding vector_cosine_ops);

-- ---------- Users & troubleshooting sessions ----------

CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id   TEXT UNIQUE,
    unlocked_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE troubleshoot_sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id),
    tutorial_id UUID REFERENCES tutorials(id),
    query       TEXT NOT NULL,
    response    TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
