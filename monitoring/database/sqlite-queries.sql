-- SQLite Performance Queries
-- For SQLite databases (auth service, notification service, etc.)

-- ============================================
-- 1. Table Information
-- ============================================
SELECT 
    name as table_name,
    type
FROM sqlite_master 
WHERE type='table'
ORDER BY name;

-- ============================================
-- 2. Index Information
-- ============================================
SELECT 
    name as index_name,
    tbl_name as table_name,
    sql
FROM sqlite_master 
WHERE type='index'
ORDER BY tbl_name;

-- ============================================
-- 3. Database Size
-- ============================================
SELECT page_count * page_size as database_size_bytes
FROM pragma_page_count(), pragma_page_size();

-- ============================================
-- 4. Table Row Counts (example for common tables)
-- ============================================
SELECT 'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'tickets' as table_name, COUNT(*) as row_count FROM tickets
UNION ALL
SELECT 'notifications' as table_name, COUNT(*) as row_count FROM notifications;

-- ============================================
-- 5. Database Integrity Check
-- ============================================
PRAGMA integrity_check;

-- ============================================
-- 6. Query Plan Analysis (use EXPLAIN QUERY PLAN)
-- Example: Analyze a specific query
-- ============================================
EXPLAIN QUERY PLAN
SELECT * FROM tickets WHERE status = 'open';

-- ============================================
-- 7. Table Schema
-- ============================================
SELECT sql FROM sqlite_master WHERE type='table' AND name='tickets';
