"""jobs.score_template — DB-backed default fit payloads for catalog jobs

Revision ID: 20260421_00
Revises: 20260420_00
Create Date: 2026-04-21
"""

import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "20260421_00"
down_revision = "20260420_00"
branch_labels = None
depends_on = None

# Previously hardcoded in jobs_service — now authoritative in DB.
_CATALOG_SCORE_TEMPLATES: dict[str, dict] = {
    "jb_cat_001": {
        "fit_score": 4.3,
        "fit_reasons": [
            "Strong overlap with AI/ML product delivery",
            "Remote EU matches common flexibility needs",
        ],
        "risk_flags": [],
        "dimension_scores": {
            "tech": 4.4,
            "culture": 4.0,
            "seniority": 4.2,
            "comp": 4.1,
            "location": 4.5,
            "channel_recommendation": "email",
        },
    },
    "jb_cat_002": {
        "fit_score": 4.1,
        "fit_reasons": ["Platform and serving experience transfers well", "Hybrid Berlin is commutable for many"],
        "risk_flags": ["Heavy on-call possible during incidents"],
        "dimension_scores": {
            "tech": 4.3,
            "culture": 3.9,
            "seniority": 4.0,
            "comp": 4.0,
            "location": 3.8,
            "channel_recommendation": "linkedin",
        },
    },
    "jb_cat_003": {
        "fit_score": 3.9,
        "fit_reasons": ["Backend scale and integrations are core to the role"],
        "risk_flags": ["Regulated domain — slower shipping cycles"],
        "dimension_scores": {
            "tech": 3.9,
            "culture": 3.8,
            "seniority": 4.1,
            "comp": 4.2,
            "location": 4.4,
            "channel_recommendation": "company_site",
        },
    },
    "jb_cat_004": {
        "fit_score": 3.7,
        "fit_reasons": ["Experimentation toolkit fits data-savvy generalists"],
        "risk_flags": ["Title says scientist — may expect deeper stats than engineering"],
        "dimension_scores": {
            "tech": 3.6,
            "culture": 3.9,
            "seniority": 3.6,
            "comp": 3.8,
            "location": 3.7,
            "channel_recommendation": "email",
        },
    },
}


def upgrade() -> None:
    op.add_column("jobs", sa.Column("score_template", sa.JSON(), nullable=True))
    conn = op.get_bind()
    # Parameterized UPDATE (compat with Postgres JSON/JSONB and SQLite offline tooling).
    for job_id, spec in _CATALOG_SCORE_TEMPLATES.items():
        conn.execute(
            text("UPDATE jobs SET score_template = CAST(:payload AS json) WHERE id = :jid"),
            {"payload": json.dumps(spec), "jid": job_id},
        )


def downgrade() -> None:
    op.drop_column("jobs", "score_template")
