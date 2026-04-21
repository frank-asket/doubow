-- Doubow: schema/data verification for Supabase/Postgres
-- Usage:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/scripts/db_verify.sql
--
-- One-command rerun (seed + verify):
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/scripts/db_seed.sql -f backend/scripts/db_verify.sql

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

\echo ''
\echo '== SEED SANITY (demo rows) =='
SELECT
  (SELECT COUNT(*)::int FROM users WHERE id LIKE 'u_demo_%') AS demo_users,
  (SELECT COUNT(*)::int FROM applications WHERE user_id LIKE 'u_demo_%') AS demo_applications,
  (SELECT COUNT(*)::int FROM approvals WHERE user_id LIKE 'u_demo_%' AND status = 'pending') AS demo_pending_approvals;

\echo ''
\echo '== ASSERTIONS (fail fast if seed not applied) =='
DO $$
DECLARE
  nu int;
  na int;
BEGIN
  SELECT COUNT(*) INTO nu FROM users WHERE id LIKE 'u_demo_%';
  SELECT COUNT(*) INTO na FROM applications WHERE user_id LIKE 'u_demo_%';
  IF nu < 2 THEN
    RAISE EXCEPTION 'db_verify: expected >= 2 demo users (u_demo_%%), got %', nu;
  END IF;
  IF na < 5 THEN
    RAISE EXCEPTION 'db_verify: expected >= 5 demo applications, got %', na;
  END IF;
END $$;
