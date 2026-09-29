--
--depends:

-- pgvector is provided by the pgvector/pgvector database image in Compose.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS pph_ai_guild_config (
    guild_id BIGINT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pph_ai_channels (
    guild_id BIGINT NOT NULL
        REFERENCES pph_ai_guild_config(guild_id) ON DELETE CASCADE,
    channel_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, channel_id)
);

CREATE TABLE IF NOT EXISTS discord_messages (
    message_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    author_is_bot BOOLEAN NOT NULL DEFAULT FALSE,
    thread_id BIGINT,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    reply_to_message_id BIGINT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS discord_messages_channel_created_idx
    ON discord_messages (guild_id, channel_id, created_at DESC);

CREATE INDEX IF NOT EXISTS discord_messages_guild_created_idx
    ON discord_messages (guild_id, created_at DESC);

CREATE TABLE IF NOT EXISTS message_embeddings (
    message_id BIGINT NOT NULL
        REFERENCES discord_messages(message_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    model_id VARCHAR(255) NOT NULL,
    dimensions INTEGER NOT NULL CHECK (dimensions > 0),
    embedding VECTOR NOT NULL,
    embedded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (message_id, chunk_index, model_id),
    CHECK (vector_dims(embedding) = dimensions)
);

CREATE TABLE IF NOT EXISTS embedding_jobs (
    message_id BIGINT PRIMARY KEY
        REFERENCES discord_messages(message_id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_error TEXT
);

CREATE INDEX IF NOT EXISTS embedding_jobs_available_idx
    ON embedding_jobs (available_at)
    WHERE status IN ('pending', 'failed');
