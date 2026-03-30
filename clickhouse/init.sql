CREATE DATABASE IF NOT EXISTS honeypot;

CREATE TABLE IF NOT EXISTS honeypot.redis_events (
    time DateTime64(6, 'UTC'),
    event String,
    ip String,
    cmd String
) ENGINE = MergeTree()
ORDER BY time;

