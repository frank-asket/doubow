# Resilience (Doubow API)

This doc matches the implementation choices for failure handling and orchestrator probes — **not** a global circuit breaker around the entire FastAPI app.

## Circuit breaking

- **OpenRouter (LLM)** — Per–use-case in-memory circuit in `backend/api_gateway/services/openrouter.py`: after consecutive failures, calls fail fast for a short cooldown, then recover. **Not shared across multiple API worker processes** (each process has its own state).
- **No app-wide breaker** — A single breaker for “the whole API” would couple unrelated failures and widen blast radius. Prefer **per-dependency** behavior (timeouts, retries where safe, readiness) and **edge** protection (rate limits, load balancers).

## Rate limiting

- **slowapi** — Default `240/minute` per client key (`user:…` from Clerk JWT `sub`, else `ip:…`). See `backend/api_gateway/main.py` and `dependencies.rate_limit_key`.

## Readiness and liveness

| Endpoint | Purpose |
|----------|---------|
| **`GET /healthz`** | **Liveness** — process is up. No DB/Redis calls; suitable for frequent probes. |
| **`GET /ready`** | **Readiness** — runs `SELECT 1` on Postgres (required). **503** if DB is down. Redis is probed but **non-fatal**: if Redis fails, response stays **200** with `"redis": "degraded"` (cache/Celery are optional). |
| **`GET /metrics`** | Prometheus metrics (exempt from app rate limit with system routes). |

Kubernetes-style usage: **livenessProbe → `/healthz`**, **readinessProbe → `/ready`**.

Implementation: `backend/api_gateway/services/health_checks.py`.

## Related

- Retries and OpenRouter streaming: `services/openrouter.py`
- Redis job list cache (optional): `services/jobs_cache.py`
- Celery (optional): `tasks/celery_app.py`
