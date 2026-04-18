-- Doubow: idempotent minimal seed for Supabase/Postgres
-- Usage:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/db_seed.sql

INSERT INTO users (id, email, name, plan)
VALUES ('u_demo_001', 'demo@doubow.ai', 'Doubow Demo', 'pro')
ON CONFLICT (email) DO NOTHING;

INSERT INTO jobs (id, source, external_id, title, company, location, description, url)
VALUES (
  'j_demo_001',
  'manual',
  'demo-001',
  'AI Product Engineer',
  'Doubow Labs',
  'Remote',
  'Demo seeded role',
  'https://doubow.ai/jobs/demo-001'
)
ON CONFLICT (source, external_id) DO NOTHING;

INSERT INTO applications (id, user_id, job_id, status, channel, notes, is_stale)
VALUES ('a_demo_001', 'u_demo_001', 'j_demo_001', 'saved', 'email', 'Seeded demo application', false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO approvals (id, user_id, application_id, type, channel, subject, draft_body, status)
VALUES (
  'ap_demo_001',
  'u_demo_001',
  'a_demo_001',
  'cover_letter',
  'email',
  'Application for AI Product Engineer',
  'Seeded draft body',
  'pending'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO autopilot_runs (id, user_id, status, scope, request_fingerprint)
VALUES ('ar_demo_001', 'u_demo_001', 'completed', 'all', 'seed-fingerprint')
ON CONFLICT (id) DO NOTHING;

INSERT INTO prep_sessions (id, user_id, application_id, questions, star_stories, company_brief)
VALUES (
  'ps_demo_001',
  'u_demo_001',
  'a_demo_001',
  '["Tell me about yourself"]'::json,
  '[]'::json,
  'Seeded company brief'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO resumes (id, user_id, storage_path, parsed_profile, preferences, version)
VALUES (
  'r_demo_001',
  'u_demo_001',
  'resumes/demo.pdf',
  '{"headline":"AI Product Engineer"}'::json,
  '{"locations":["Remote"]}'::json,
  1
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO job_scores (id, user_id, job_id, fit_score, fit_reasons, risk_flags, dimension_scores)
VALUES (
  'js_demo_001',
  'u_demo_001',
  'j_demo_001',
  4.6,
  '["Strong product+AI fit"]'::json,
  '[]'::json,
  '{"tech_match":4.8,"seniority":4.4}'::json
)
ON CONFLICT ON CONSTRAINT uq_job_scores_user_job DO NOTHING;
