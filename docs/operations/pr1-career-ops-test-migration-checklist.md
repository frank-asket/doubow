# PR1 Verification Checklist - Career Ops Backend Contracts + Telemetry

Purpose: verify PR1 backend integrity before merge (migrations, API contracts, telemetry, and tests).

Owner: Backend engineering

---

## 1) Migration verification

- [ ] From repo root, confirm new migration chain is present:
  - `backend/api_gateway/db/migrations/versions/20260506_00_career_ops_scan_runs.py`
  - `backend/api_gateway/db/migrations/versions/20260506_01_career_ops_scan_run_source.py`
- [ ] Run migration upgrade in backend environment:
  - `alembic upgrade head`
- [ ] Confirm `career_ops_scan_runs` table exists.
- [ ] Confirm `source` column exists in `career_ops_scan_runs`.
- [ ] Confirm index `ix_career_ops_scan_runs_source` exists.
- [ ] Run rollback/forward smoke:
  - `alembic downgrade -1`
  - `alembic upgrade head`

Evidence:
- [ ] Paste migration logs in PR comment.
- [ ] Paste SQL output for table + column + index checks.

Tiny Postgres SQL snippets (copy-paste):

```sql
-- 1) table exists
SELECT to_regclass('public.career_ops_scan_runs') AS table_name;

-- 2) source column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'career_ops_scan_runs'
  AND column_name = 'source';

-- 3) source index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'career_ops_scan_runs'
  AND indexname = 'ix_career_ops_scan_runs_source';
```

---

## 2) Backend test verification

- [ ] Run focused scan tests:
  - `pytest backend/api_gateway/tests/test_career_ops_scan.py -q`
- [ ] Confirm new test passes:
  - `test_scan_history_persists_source_field`
- [ ] Run telemetry suite:
  - `pytest backend/api_gateway/tests/test_telemetry.py -q`
- [ ] Run provider/jobs suite impacted by router changes:
  - `pytest backend/api_gateway/tests/test_job_provider_ingestion.py -q`

Evidence:
- [ ] Attach command outputs (or CI links) for all three suites.

---

## 3) API contract verification

- [ ] `POST /v1/jobs/scan/run` accepts `source`, `query`, `location`, thresholds.
- [ ] `GET /v1/jobs/scan/runs` includes persisted `source` in history items.
- [ ] Failure path returns `status=failed` + `error_code`.

Manual smoke script:
- [ ] Create an authenticated request with `source="discover_page"`.
- [ ] Confirm response includes `scan_run_id`.
- [ ] Fetch `/v1/jobs/scan/runs?limit=1`.
- [ ] Confirm top run has `source="discover_page"`.

---

## 4) Telemetry integrity verification

- [ ] Confirm lifecycle events are backend-emitted (no duplicate frontend lifecycle tracking):
  - `career_ops_scan_started`
  - `career_ops_scan_completed`
  - `career_ops_scan_failed`
- [ ] Confirm lifecycle event properties include:
  - `scan_run_id`
  - `source`
  - `query`
  - `location`
  - `min_fit_threshold`
- [ ] Confirm threshold and queue events still emit:
  - `career_ops_threshold_applied`
  - `career_ops_queue_top_n_clicked` (when `queue_top_n > 0`)

Evidence:
- [ ] Add sample telemetry payloads from logs/DB for success and failure runs.

---

## 5) Merge gate

- [ ] Migrations apply cleanly on staging.
- [ ] Focused backend tests pass.
- [ ] API contract smoke passed.
- [ ] Telemetry payload spot-check passed.
- [ ] PR description updated with evidence links.
