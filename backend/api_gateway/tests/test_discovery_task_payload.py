from tasks.discovery_task import _normalize_job_payload


def test_normalize_job_payload_drops_malformed_url_fields() -> None:
    payload = _normalize_job_payload(
        [
            {
                "source": "manual",
                "external_id": "disc-x",
                "title": "Backend Engineer",
                "company": "Acme",
                "url": "javascript:alert(1)",
                "logo_url": "ftp://bad.example.com/logo.png",
                "description": "Role description",
            }
        ]
    )

    job = payload.jobs[0]
    assert job.url == ""
    assert job.logo_url is None


def test_normalize_job_payload_keeps_valid_https_urls() -> None:
    payload = _normalize_job_payload(
        [
            {
                "source": "manual",
                "external_id": "disc-y",
                "title": "Platform Engineer",
                "company": "Acme",
                "url": "https://acme.example/jobs/123",
                "logo_url": "https://cdn.example/logo.png",
                "description": "Role description",
            }
        ]
    )

    job = payload.jobs[0]
    assert job.url == "https://acme.example/jobs/123"
    assert job.logo_url == "https://cdn.example/logo.png"
