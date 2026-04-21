-- Optional: least-privilege API role so PostgreSQL RLS applies (superuser bypasses RLS).
-- Run once as a superuser / Supabase SQL editor role that can CREATE ROLE.
-- Replace APP_PASSWORD before execution; wire FastAPI DATABASE_URL to this role in production-like envs.
--
--   psql "$SUPERUSER_DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/scripts/db_grant_app_role.sql

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'doubow_app') THEN
    CREATE ROLE doubow_app LOGIN PASSWORD 'changeme_replace_in_vault';
  END IF;
END $$;

DO $$
BEGIN
  EXECUTE format(
    'GRANT CONNECT ON DATABASE %I TO doubow_app',
    current_database()
  );
END $$;

GRANT USAGE ON SCHEMA public TO doubow_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO doubow_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO doubow_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO doubow_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO doubow_app;
