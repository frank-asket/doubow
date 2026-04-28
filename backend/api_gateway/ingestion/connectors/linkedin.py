from __future__ import annotations

import hashlib
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import AsyncIterator
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

from ingestion.connectors.base import BaseConnector, RawJob

SEARCH_QUERIES = [
    "machine learning engineer",
    "ai engineer",
    "llm engineer",
    "mlops engineer",
    "data scientist",
]


class LinkedInConnector(BaseConnector):
    source_name = "linkedin"
    rate_limit_rps = 0.3

    async def fetch(self) -> AsyncIterator[RawJob]:
        for query in SEARCH_QUERIES:
            rss_url = (
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?keywords={quote_plus(query)}&f_TPR=r86400&f_WT=2"
            )
            # Guest HTML endpoint can block; RSS endpoint tends to be more stable.
            fallback_rss = (
                "https://www.linkedin.com/jobs/search.rss"
                f"?keywords={quote_plus(query)}&f_TPR=r86400&f_WT=2"
            )
            for url in (fallback_rss, rss_url):
                try:
                    response = await self._get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 (compatible; doubow-ingestion/1.0)"},
                        follow_redirects=True,
                    )
                except Exception:
                    continue
                jobs = self._parse_rss(response.text, query)
                if jobs:
                    for job in jobs:
                        yield job
                    break

    def _parse_rss(self, raw_xml: str, query: str) -> list[RawJob]:
        items: list[RawJob] = []
        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError:
            return items
        channel = root.find("channel")
        if channel is None:
            return items
        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            if not title or not link:
                continue
            company = "Unknown"
            job_title = title
            if " at " in title:
                left, right = title.split(" at ", 1)
                job_title, company = left.strip(), right.strip()
            ext_id = hashlib.md5(link.encode()).hexdigest()[:16]
            items.append(
                RawJob(
                    source=self.source_name,
                    external_id=ext_id,
                    title=job_title,
                    company=company,
                    url=link,
                    description=description or job_title,
                    location="",
                    remote=True,
                    posted_at=self._parse_rfc2822(pub_date),
                    tags=[query],
                    employment_type="full_time",
                    extra={"via": "rss", "query": query},
                )
            )
        return items

    @staticmethod
    def _parse_rfc2822(raw: str) -> datetime | None:
        if not raw:
            return None
        try:
            return parsedate_to_datetime(raw)
        except Exception:
            return None

