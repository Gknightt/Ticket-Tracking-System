-- Database Performance Analysis Queries
-- For PostgreSQL databases

-- ============================================
-- 1. Table Size and Row Counts
-- ============================================
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================
-- 2. Index Usage Statistics
-- ============================================
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- ============================================
-- 3. Slow Query Detection (requires pg_stat_statements)
-- ============================================
-- Enable with: CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- ============================================
-- 4. Cache Hit Ratio (should be > 99%)
-- ============================================
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 AS cache_hit_ratio
FROM pg_statio_user_tables;

-- ============================================
-- 5. Active Connections
-- ============================================
SELECT
    datname,
    count(*) as connections,
    max(state) as state
FROM pg_stat_activity
WHERE state IS NOT NULL
GROUP BY datname;

-- ============================================
-- 6. Table Bloat Detection
-- ============================================
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_tuple_percent
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC;

-- ============================================
-- 7. Missing Indexes (tables with sequential scans)
-- ============================================
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan AS avg_seq_tup_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
  AND idx_scan = 0
  AND schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY seq_tup_read DESC
LIMIT 20;

-- ============================================
-- 8. Database Size
-- ============================================
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
ORDER BY pg_database_size(datname) DESC;
