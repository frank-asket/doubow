SHELL := /bin/bash

PYTHON ?= python3
ALEMBIC_CONFIG := baseline/api_gateway/alembic.ini
API_PY_PATH := baseline/api_gateway

.PHONY: db-migrate db-seed db-verify db-sync

db-migrate:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@PYTHONPATH="$(API_PY_PATH)" \
	DATABASE_URL="$${DATABASE_URL}" \
	ALEMBIC_DATABASE_URL="$${DATABASE_URL}" \
	$(PYTHON) -m alembic -c "$(ALEMBIC_CONFIG)" upgrade head

db-seed:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@psql "$$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/db_seed.sql

db-verify:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	@psql "$$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/db_verify.sql

db-sync: db-migrate db-seed db-verify
	@echo "Doubow DB sync complete."
