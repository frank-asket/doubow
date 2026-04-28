SHELL := /bin/bash

PYTHON ?= python3
ALEMBIC_CONFIG := api_gateway/alembic.ini
API_PY_PATH := api_gateway

.PHONY: db-migrate db-migrate-safe db-seed db-verify db-sync db-reset-demo api-test-autopilot-parity api-test-autopilot launch-probe auth-probe jobs-cache-preview jobs-cache-invalidate

# libpq/psql does not accept SQLAlchemy async URLs (postgresql+asyncpg://). Strip the driver for psql targets.
define PSQL_CMD
bash -ec 'PU=$$(echo "$$DATABASE_URL" | sed -e "s|^postgresql+asyncpg://|postgresql://|" -e "s|^postgres+asyncpg://|postgresql://|"); psql "$$PU" -v ON_ERROR_STOP=1 $(1)'
endef

# Uses `uv` + api_gateway deps so Alembic does not need a global install (see backend/api_gateway).
db-migrate:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@cd "$(API_PY_PATH)" && PYTHONPATH=. \
		DATABASE_URL="$${DATABASE_URL}" \
		ALEMBIC_DATABASE_URL="$${DATABASE_URL}" \
		uv run --with-requirements requirements.txt python -m alembic -c alembic.ini upgrade head

# Alembic-safe migration helper:
# - strips async driver suffixes for sync psycopg2 migration path
# - rewrites ?ssl=... to psycopg2-compatible ?sslmode=...
db-migrate-safe:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@SAFE_DB_URL=$$($(PYTHON) -c "from urllib.parse import urlparse,parse_qsl,urlencode,urlunparse; import os; raw=os.environ['DATABASE_URL'].strip(); u=urlparse(raw); scheme=u.scheme.replace('postgresql+asyncpg','postgresql').replace('postgres+asyncpg','postgresql'); params=[('sslmode', 'require' if (v or '').lower() in {'1','true','yes','require'} else 'disable') if k=='ssl' else (k,v) for k,v in parse_qsl(u.query, keep_blank_values=True)]; print(urlunparse((scheme,u.netloc,u.path,u.params,urlencode(params),u.fragment)))"); \
	cd "$(API_PY_PATH)" && PYTHONPATH=. \
		DATABASE_URL="$$SAFE_DB_URL" \
		ALEMBIC_DATABASE_URL="$$SAFE_DB_URL" \
		uv run --with-requirements requirements.txt python -m alembic -c alembic.ini upgrade head

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

# Focused autopilot parity test (legacy runner vs LangGraph nodes produce identical item_results).
api-test-autopilot-parity:
	@cd "$(API_PY_PATH)" && PYTHONPATH=. \
		uv run \
			--with-requirements requirements.txt \
			--with pytest \
			--with pytest-asyncio \
			--with aiosqlite \
			python -m pytest tests/test_autopilot_execution.py -k "langgraph_and_legacy_produce_identical_item_results" -q

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
