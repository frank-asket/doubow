SHELL := /bin/bash

PYTHON ?= python3
ALEMBIC_CONFIG := baseline/api_gateway/alembic.ini
API_PY_PATH := baseline/api_gateway

.PHONY: db-migrate db-seed db-verify db-sync db-reset-demo

# libpq/psql does not accept SQLAlchemy async URLs (postgresql+asyncpg://). Strip the driver for psql targets.
define PSQL_CMD
bash -ec 'PU=$$(echo "$$DATABASE_URL" | sed -e "s|^postgresql+asyncpg://|postgresql://|" -e "s|^postgres+asyncpg://|postgresql://|"); psql "$$PU" -v ON_ERROR_STOP=1 $(1)'
endef

# Uses `uv` + api_gateway deps so Alembic does not need a global install (see baseline/api_gateway).
db-migrate:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@cd "$(API_PY_PATH)" && PYTHONPATH=. \
		DATABASE_URL="$${DATABASE_URL}" \
		ALEMBIC_DATABASE_URL="$${DATABASE_URL}" \
		uv run python -m alembic -c alembic.ini upgrade head

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
