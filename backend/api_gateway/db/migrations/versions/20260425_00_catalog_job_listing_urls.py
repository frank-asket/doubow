"""Replace example.com catalog job URLs with LinkedIn job-search keywords links.

Revision ID: 20260425_00
Revises: 20260424_00
Create Date: 2026-04-21
"""

from urllib.parse import quote_plus

from alembic import op
from sqlalchemy import text

revision = "20260425_00"
down_revision = "20260424_00"
branch_labels = None
depends_on = None


def _keywords(title: str, company: str) -> str:
    return quote_plus(f"{title} {company}")


def upgrade() -> None:
    conn = op.get_bind()
    rows = [
        ("jb_cat_001", "Senior AI Product Engineer", "Northwind Labs"),
        ("jb_cat_002", "ML Platform Engineer", "Riverstone"),
        ("jb_cat_003", "Staff Backend Engineer", "Cobalt Health"),
        ("jb_cat_004", "Data Scientist — Growth", "Lumen Apps"),
    ]
    for jid, title, company in rows:
        kw = _keywords(title, company)
        url = f"https://www.linkedin.com/jobs/search/?keywords={kw}"
        conn.execute(text("UPDATE jobs SET url = :url WHERE id = :jid"), {"url": url, "jid": jid})


def downgrade() -> None:
    conn = op.get_bind()
    for jid, path in [
        ("jb_cat_001", "https://example.com/jobs/jb_cat_001"),
        ("jb_cat_002", "https://example.com/jobs/jb_cat_002"),
        ("jb_cat_003", "https://example.com/jobs/jb_cat_003"),
        ("jb_cat_004", "https://example.com/jobs/jb_cat_004"),
    ]:
        conn.execute(text("UPDATE jobs SET url = :url WHERE id = :jid"), {"url": path, "jid": jid})
