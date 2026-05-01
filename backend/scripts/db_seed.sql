-- Doubow: richer multi-user seed for Supabase/Postgres (idempotent).
-- Depends on migrations: catalog jobs jb_cat_001–jb_cat_004 (source=catalog).
-- Run via: make -C backend db-seed (uses scripts/normalize_database_url.py for psql).

-- ─── Users ─────────────────────────────────────────────────────────────────
INSERT INTO users (id, email, name, plan)
VALUES
  ('u_demo_001', 'demo@doubow.ai', 'Doubow Demo', 'pro'),
  ('u_demo_002', 'sandbox@doubow.ai', 'Sandbox User', 'free')
ON CONFLICT (email) DO NOTHING;

-- ─── Extra jobs (besides migration catalog jb_cat_*) ─────────────────────────
INSERT INTO jobs (id, source, external_id, title, company, location, salary_range, description, url)
VALUES
  (
    'j_demo_001',
    'manual',
    'demo-001',
    'AI Product Engineer',
    'Doubow Labs',
    'Remote',
    '€130k–€155k',
    'Demo seeded role focused on AI product surfaces.',
    'https://doubow.ai/jobs/demo-001'
  ),
  (
    'j_demo_002',
    'manual',
    'demo-002',
    'Senior ML Engineer',
    'Northwind Applied',
    'Berlin · Hybrid',
    '€115k–€140k',
    'Batch inference and feature pipelines.',
    'https://example.com/jobs/j_demo_002'
  ),
  (
    'j_demo_003',
    'manual',
    'demo-003',
    'Staff Backend Engineer',
    'Cobalt Health EU',
    'Remote · EU',
    '€125k–€145k',
    'APIs and clinical data integrations.',
    'https://example.com/jobs/j_demo_003'
  )
ON CONFLICT (source, external_id) DO NOTHING;

-- ─── Applications (mix of statuses for Pipeline / Prep) ─────────────────────
INSERT INTO applications (id, user_id, job_id, status, channel, notes, is_stale, applied_at)
VALUES
  ('a_demo_001', 'u_demo_001', 'j_demo_001', 'saved', 'email', 'Primary seeded row', false, NULL),
  ('a_demo_002', 'u_demo_001', 'jb_cat_001', 'pending', 'email', 'Queued — high fit catalog role', false, NULL),
  ('a_demo_003', 'u_demo_001', 'jb_cat_002', 'interview', 'linkedin', 'Interview scheduled', false, NOW() AT TIME ZONE 'utc' - INTERVAL '3 days'),
  ('a_demo_004', 'u_demo_001', 'jb_cat_003', 'applied', 'company_site', 'Applied awaiting reply', false, NOW() AT TIME ZONE 'utc' - INTERVAL '10 days'),
  ('a_demo_005', 'u_demo_001', 'j_demo_002', 'pending', 'email', 'Pipeline pending', false, NULL),
  ('a_demo_006', 'u_demo_001', 'jb_cat_004', 'rejected', 'email', 'Archived application', false, NOW() AT TIME ZONE 'utc' - INTERVAL '40 days'),
  ('a_demo_007', 'u_demo_002', 'j_demo_003', 'saved', 'linkedin', 'Second-user sandbox row', false, NULL)
ON CONFLICT (id) DO NOTHING;

-- ─── Approvals (pending drafts for Approvals UI) ──────────────────────────────
INSERT INTO approvals (id, user_id, application_id, type, channel, subject, draft_body, status, delivery_status)
VALUES
  (
    'ap_demo_001',
    'u_demo_001',
    'a_demo_001',
    'cover_letter',
    'email',
    'Application — AI Product Engineer · Demo',
    'Dear hiring team,\n\nI bring 6+ years shipping production ML and RAG systems. Attached is my background aligned to your stack.\n\nBest,\nDemo User',
    'pending',
    'not_sent'
  ),
  (
    'ap_demo_002',
    'u_demo_001',
    'a_demo_002',
    'cover_letter',
    'email',
    'Application — Senior AI Product Engineer',
    'Hi — I am excited about the charter described in your posting. I led evaluation harnesses and agent deployments at scale.\n\nBest,\nDemo User',
    'pending',
    'not_sent'
  ),
  (
    'ap_demo_003',
    'u_demo_001',
    'a_demo_005',
    'linkedin_note',
    'linkedin',
    NULL,
    'Hi — I applied for the ML role and would love to share a concise note on retrieval pipelines we shipped to prod.',
    'pending',
    'not_sent'
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO autopilot_runs (id, user_id, status, scope, request_fingerprint)
VALUES ('ar_demo_001', 'u_demo_001', 'completed', 'all', 'seed-fingerprint')
ON CONFLICT (id) DO NOTHING;

INSERT INTO prep_sessions (id, user_id, application_id, questions, star_stories, company_brief)
VALUES (
  'ps_demo_001',
  'u_demo_001',
  'a_demo_003',
  '[
    "Walk me through a retrieval stack you shipped end-to-end.",
    "Latency vs recall — how did you tune HNSW + rerank?",
    "Describe a silent failure you debugged in agentic workloads."
  ]'::json,
  '[]'::json,
  'Company brief: emphasize API-first culture and multilingual retrieval investments.'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO resumes (id, user_id, storage_path, parsed_profile, preferences, version)
VALUES (
  'r_demo_001',
  'u_demo_001',
  'resumes/demo.pdf',
  '{"headline":"AI Product Engineer","skills":["Python","FastAPI","LLMs"],"experience_years":8}'::json,
  '{"target_role":"AI / ML Engineer","location":"Remote / Europe","skills":["RAG","LLMs"],"seniority":"Senior"}'::json,
  2
)
ON CONFLICT (id) DO NOTHING;

-- ─── Job scores (explicit scores for seeded users; skips if already present) ─
INSERT INTO job_scores (id, user_id, job_id, fit_score, fit_reasons, risk_flags, dimension_scores, provenance)
VALUES
  (
    'js_demo_001',
    'u_demo_001',
    'j_demo_001',
    4.6,
    '["Strong product + AI overlap"]'::json,
    '[]'::json,
    '{"tech":4.8,"culture":4.5,"seniority":4.6,"comp":4.4,"location":4.7,"channel_recommendation":"email"}'::json,
    'template_seeded'
  ),
  (
    'js_demo_seed_cat1',
    'u_demo_001',
    'jb_cat_001',
    4.8,
    '["Catalog: strong JD fit from seed"]'::json,
    '[]'::json,
    '{"tech":4.9,"culture":4.7,"seniority":4.8,"comp":4.6,"location":4.9,"channel_recommendation":"email"}'::json,
    'template_seeded'
  ),
  (
    'js_demo_seed_cat2',
    'u_demo_001',
    'jb_cat_002',
    4.5,
    '["Platform overlap"]'::json,
    '["On-call load possible"]'::json,
    '{"tech":4.6,"culture":4.4,"seniority":4.5,"comp":4.5,"location":4.6,"channel_recommendation":"linkedin"}'::json,
    'template_seeded'
  ),
  (
    'js_demo_seed_u2',
    'u_demo_002',
    'j_demo_003',
    3.9,
    '["Backend + regulated domain fit"]'::json,
    '[]'::json,
    '{"tech":3.9,"culture":3.8,"seniority":4.0,"comp":4.1,"location":4.2,"channel_recommendation":"company_site"}'::json,
    'template_seeded'
  )
ON CONFLICT ON CONSTRAINT uq_job_scores_user_job DO NOTHING;
