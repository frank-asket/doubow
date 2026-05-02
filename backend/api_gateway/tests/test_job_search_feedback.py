"""Unit tests for outcome-derived feedback snapshots."""

from services.job_search_feedback import compute_feedback_snapshot


def test_feedback_snapshot_counts_and_hints():
    snap = compute_feedback_snapshot(
        {"saved": 8, "applied": 2, "interview": 1, "offer": 0, "rejected": 4},
        trace_id="trace-x",
    )
    assert snap["version"] == 1
    assert snap["trace_id"] == "trace-x"
    assert snap["counts"]["applied"] == 2
    assert "matching_blend_hints" in snap
    assert "semantic_matching_delta" in snap["matching_blend_hints"]
    assert isinstance(snap["insights"], list)


def test_feedback_snapshot_empty_pipeline():
    snap = compute_feedback_snapshot({}, trace_id=None)
    assert snap["totals"]["applications_tracked"] == 0
    assert any("No applications yet" in n for n in snap["insights"])
