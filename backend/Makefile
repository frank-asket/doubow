SHELL := /bin/bash

PYTHON ?= python3
ALEMBIC_CONFIG := api_gateway/alembic.ini
API_PY_PATH := api_gateway

.PHONY: db-migrate db-seed db-verify db-sync db-reset-demo api-test-autopilot-parity api-test-autopilot

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
