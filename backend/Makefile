SHELL := /bin/bash

PYTHON ?= python3
ALEMBIC_CONFIG := api_gateway/alembic.ini
API_PY_PATH := api_gateway
NORMALIZE_DB_URL := $(PYTHON) scripts/normalize_database_url.py

.PHONY: db-migrate db-migrate-safe db-seed db-verify db-sync db-sync-safe db-reset-demo api-test-autopilot-parity api-test-autopilot api-test-job-search-contracts launch-probe auth-probe monitoring-drill-report jobs-cache-preview jobs-cache-invalidate

# libpq/psql: normalize URL (asyncpg scheme + ssl= → sslmode=). See scripts/normalize_database_url.py.
define PSQL_CMD
bash -ec 'PU=$$($(NORMALIZE_DB_URL)); psql "$$PU" -v ON_ERROR_STOP=1 $(1)'
endef

# Uses `uv` + api_gateway deps. URL is normalized for psycopg2 (asyncpg scheme + ssl= query).
db-migrate:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@SAFE_DB_URL=$$($(NORMALIZE_DB_URL)); \
	cd "$(API_PY_PATH)" && PYTHONPATH=. \
		DATABASE_URL="$$SAFE_DB_URL" \
		ALEMBIC_DATABASE_URL="$$SAFE_DB_URL" \
		uv run --with-requirements requirements.txt python -m alembic -c alembic.ini upgrade head

# Alias: same as db-migrate (kept for scripts/docs that mention db-migrate-safe).
db-migrate-safe: db-migrate

db-seed:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@$(call PSQL_CMD,-f scripts/db_seed.sql)

db-verify:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@$(call PSQL_CMD,-f scripts/db_verify.sql)

# Dev/staging: removes u_demo_* users and j_demo_* jobs only (see scripts/db_reset_demo.sql), then re-seeds.
db-reset-demo:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@$(call PSQL_CMD,-f scripts/db_reset_demo.sql)
	@$(MAKE) db-seed

db-sync: db-migrate db-seed db-verify
	@echo "Doubow DB sync complete."

# Alias: same as db-sync (migrate + seed + verify all use normalized URLs).
db-sync-safe: db-sync

# Focused autopilot parity test (legacy runner vs LangGraph nodes produce identical item_results).
api-test-autopilot-parity:
	@cd "$(API_PY_PATH)" && PYTHONPATH=. \
		uv run \
			--with-requirements requirements.txt \
			--with pytest \
			--with pytest-asyncio \
			--with aiosqlite \
			python -m pytest tests/test_autopilot_execution.py -k "langgraph_and_legacy_produce_identical_item_results" -q

# Job-search pipeline + feedback-learning production contracts (fast).
api-test-job-search-contracts:
	@cd "$(API_PY_PATH)" && PYTHONPATH=. \
		uv run \
			--with-requirements requirements.txt \
			--with pytest \
			--with pytest-asyncio \
			--with aiosqlite \
			python -m pytest tests/test_production_job_search_contracts.py -q

# Full autopilot suite (idempotency/service + scope resolution + execution/parity).
api-test-autopilot:
	@cd "$(API_PY_PATH)" && PYTHONPATH=. \
		uv run \
			--with-requirements requirements.txt \
			--with pytest \
			--with pytest-asyncio \
			--with aiosqlite \
			python -m pytest \
				tests/test_autopilot.py \
				tests/test_autopilot_scopes.py \
				tests/test_autopilot_langgraph.py \
				tests/test_autopilot_execution.py -q

# Production launch gate probe (requires Clerk JWT in env var DOUBOW_LAUNCH_PROBE_TOKEN).
launch-probe:
	@cd .. && \
		python3 scripts/launch_gate_probe.py \
			--base-url "$${LAUNCH_PROBE_BASE_URL:-https://doubow-production.up.railway.app}" \
			--iterations "$${LAUNCH_PROBE_ITERATIONS:-20}" \
			--sleep-seconds "$${LAUNCH_PROBE_SLEEP_SECONDS:-2.0}" \
			--token-env "$${LAUNCH_PROBE_TOKEN_ENV:-DOUBOW_LAUNCH_PROBE_TOKEN}"

# Auth/session gate probe (P0-2) for production launch readiness.
auth-probe:
	@cd .. && \
		python3 scripts/auth_gate_probe.py \
			--base-url "$${LAUNCH_PROBE_BASE_URL:-https://doubow-production.up.railway.app}" \
			--iterations "$${AUTH_PROBE_ITERATIONS:-10}" \
			--sleep-seconds "$${AUTH_PROBE_SLEEP_SECONDS:-1.0}" \
			--token-env "$${LAUNCH_PROBE_TOKEN_ENV:-DOUBOW_LAUNCH_PROBE_TOKEN}"

# Day 18 monitoring drill evidence snapshot + MTTD calculator.
monitoring-drill-report:
	@cd .. && \
		python3 scripts/monitoring_drill_report.py \
			--base-url "$${LAUNCH_PROBE_BASE_URL:-https://doubow-production.up.railway.app}" \
			$${DRILL_INCIDENT_STARTED_AT:+--incident-started-at "$${DRILL_INCIDENT_STARTED_AT}"} \
			$${DRILL_ALERT_DETECTED_AT:+--alert-detected-at "$${DRILL_ALERT_DETECTED_AT}"} \
			$${DRILL_ONCALL_OWNER:+--oncall-owner "$${DRILL_ONCALL_OWNER}"} \
			--output "$${DRILL_REPORT_OUTPUT:-docs/operations/evidence/day18-monitoring-drill.md}"

# Jobs list cache ops helper (safe default: dry-run).
jobs-cache-preview:
	@cd "$(API_PY_PATH)" && PYTHONPATH=. \
		uv run --with-requirements requirements.txt python ../scripts/invalidate_jobs_cache.py \
			--pattern "$${JOBS_CACHE_PATTERN:-jobs:list:*}" \
			$${JOBS_CACHE_USER_ID:+--user-id "$${JOBS_CACHE_USER_ID}"} \
			--max-keys "$${JOBS_CACHE_MAX_KEYS:-5000}"

# Destructive variant: use intentionally after backfills/upserts.
jobs-cache-invalidate:
	@cd "$(API_PY_PATH)" && PYTHONPATH=. \
		uv run --with-requirements requirements.txt python ../scripts/invalidate_jobs_cache.py \
			--pattern "$${JOBS_CACHE_PATTERN:-jobs:list:*}" \
			$${JOBS_CACHE_USER_ID:+--user-id "$${JOBS_CACHE_USER_ID}"} \
			--max-keys "$${JOBS_CACHE_MAX_KEYS:-5000}" \
			--execute
