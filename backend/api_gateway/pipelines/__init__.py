"""Ingestion and transform pipelines (namespace for Doubow’s data → LLM flows).

Implementations remain in ``services/`` to avoid circular imports and churn:

- **Jobs**: ``services.job_provider_ingestion_service``, ``services.job_discovery_service``
- **Resume**: ``services.resume_parser``, ``services.resume_service``
- **Matching / scoring**: ``services.llm_job_match_service``, ``services.semantic_match_service``

Use this package when adding orchestration modules that compose those steps.
"""

__all__: list[str] = []
