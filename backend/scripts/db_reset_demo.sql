-- Reset Doubow **demo seed data only** (users id u_demo_* and manual jobs j_demo_*).
-- Does not delete migration catalog rows (jb_cat_*) or alembic_version.
-- Run before re-seeding for a clean local/staging sandbox.
--
-- Usage (sync URL works best with psql):
--   psql "$(echo "$DATABASE_URL" | sed 's|postgresql+asyncpg://|postgresql://|')" … -f backend/scripts/db_reset_demo.sql

BEGIN;

DELETE FROM prep_sessions WHERE user_id LIKE 'u_demo_%';
DELETE FROM approvals WHERE user_id LIKE 'u_demo_%';

-- Applications reference jobs — remove before orphan job cleanup.
DELETE FROM applications WHERE user_id LIKE 'u_demo_%';

DELETE FROM autopilot_runs WHERE user_id LIKE 'u_demo_%';
DELETE FROM job_scores WHERE user_id LIKE 'u_demo_%';
DELETE FROM job_dismissals WHERE user_id LIKE 'u_demo_%';
DELETE FROM resumes WHERE user_id LIKE 'u_demo_%';

DELETE FROM users WHERE id LIKE 'u_demo_%';

DELETE FROM jobs WHERE id LIKE 'j_demo_%';

COMMIT;
