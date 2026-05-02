# Production verification — job search pipeline & feedback learning

Use after deploying changes that touch `JobSearchPipelineCoordinator`, `feedback_learning`, or matching-blend metrics.

## 1. Automated contracts (CI / local)

From repo root:

```bash
make -C backend api-test-job-search-contracts
```

This runs `tests/test_production_job_search_contracts.py`: capabilities list, assistant keyword routing, Prometheus label registration, and **feedback-learning preference routes return 200 in production when a résumé exists** (404 only if no résumé).

## 2. Live API smoke (staging / production)

Requires a valid **Clerk JWT** for a real user.

```bash
export DOUBOW_API_BASE="https://<your-api-host>"
export DOUBOW_API_TOKEN="<paste JWT>"

python3 scripts/job_search_production_smoke.py
# Optional: --staging skips GET /v1/me/preferences/feedback-learning
```

| Check | Expect |
|-------|--------|
| `GET /healthz` | 200 |
| `GET /v1/agents/capabilities` | Includes **`run_job_search_pipeline`** |
| `GET /v1/me/preferences/feedback-learning` | **200** (has résumé) or **404** (no résumé) — not 5xx |
| `GET /metrics` | Contains **`doubow_matching_blend_score_sync_total`** |

Use **`--staging`** on the smoke script only if you need to skip the feedback-learning GET (e.g. token without a user résumé on that host).

## 3. Assistant manual smoke

In **`/messages`**:

1. Send **`/pipeline-run`** — streamed response should include stage lines from **`run_job_search_pipeline`** (tool_call / tool_result / summary text).
2. Send **“run job search pipeline”** — same tool without slash.

## 4. Metrics spot-check (Prometheus / Grafana)

After users have rescored with persisted **`feedback_learning`**:

- Query `doubow_matching_blend_score_sync_total` with `personalized_blend="yes"` for outcome-driven blend activity.

## 5. Catalog refresh stage

Full **`data_collection`** with **`trigger_catalog_refresh`** requires **`JOB_CATALOG_INGESTION_USER_ID`** and provider keys in the deployment env. If unset, the stage fails fast with a documented error — not a smoke script failure unless you explicitly run the pipeline with refresh.
