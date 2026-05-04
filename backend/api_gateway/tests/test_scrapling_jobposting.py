"""JSON-LD JobPosting extraction (no network)."""

from services.scrapling_jobposting import extract_jobposting_dicts_from_html


SAMPLE_LD = """
<!DOCTYPE html><html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "Platform Engineer",
  "url": "https://careers.example.com/jobs/99",
  "datePosted": "2026-01-01",
  "description": "Build systems.",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "Contoso Labs",
    "logo": "https://careers.example.com/logo.png"
  },
  "jobLocation": { "@type": "Place", "name": "Berlin" }
}
</script>
</head><body></body></html>
"""


def test_extract_jobposting_from_ld_json():
    rows = extract_jobposting_dicts_from_html(SAMPLE_LD, page_url="https://careers.example.com/")
    assert len(rows) == 1
    r = rows[0]
    assert r["title"] == "Platform Engineer"
    assert r["company"] == "Contoso Labs"
    assert r["url"] == "https://careers.example.com/jobs/99"
    assert r["logo_url"] == "https://careers.example.com/logo.png"
    assert r["location"] == "Berlin"


def test_extract_graph_with_jobposting():
    html = """
    <script type="application/ld+json">
    {"@context":"https://schema.org","@graph":[
      {"@type":"Organization","name":"Ignore"},
      {"@type":"JobPosting","title":"QA","url":"https://x.test/q","hiringOrganization":{"@type":"Organization","name":"Zed"}}
    ]}
    </script>
    """
    rows = extract_jobposting_dicts_from_html(html, page_url="https://x.test/")
    assert len(rows) == 1
    assert rows[0]["title"] == "QA"
    assert rows[0]["company"] == "Zed"
