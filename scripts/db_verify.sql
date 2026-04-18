-- Doubow: schema/data verification for Supabase/Postgres
-- Usage:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/db_verify.sql
--
-- One-command rerun (seed + verify):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/db_seed.sql -f scripts/db_verify.sql

\echo ''
\echo '== TABLES =='
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'alembic_version',
    'users',
    'resumes',
    'jobs',
    'applications',
    'approvals',
    'autopilot_runs',
    'prep_sessions',
    'job_scores'
  )
ORDER BY tablename;

\echo ''
\echo '== ROW COUNTS =='
SELECT 'alembic_version' AS table_name, count(*)::int AS rows FROM alembic_version
UNION ALL SELECT 'users', count(*)::int FROM users
UNION ALL SELECT 'resumes', count(*)::int FROM resumes
UNION ALL SELECT 'jobs', count(*)::int FROM jobs
UNION ALL SELECT 'applications', count(*)::int FROM applications
UNION ALL SELECT 'approvals', count(*)::int FROM approvals
UNION ALL SELECT 'autopilot_runs', count(*)::int FROM autopilot_runs
UNION ALL SELECT 'prep_sessions', count(*)::int FROM prep_sessions
UNION ALL SELECT 'job_scores', count(*)::int FROM job_scores
ORDER BY table_name;

\echo ''
\echo '== ALEMBIC REVISION =='
SELECT version_num FROM alembic_version;
