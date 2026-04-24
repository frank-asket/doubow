#!/usr/bin/env python3
"""Offline evaluator for baseline vs semantic-blend precision.

This is a lightweight Phase 3 experiment helper.

Labeling modes:
- template: relevant(job) := job.score_template.fit_score >= threshold
- outcome: relevant(job) := user-level pipeline outcomes indicate positive intent/progression
- auto: prefer outcome labels when enough rows exist, otherwise fallback to template

Usage:
  ./.venv-test/bin/python scripts/semantic_precision_eval.py --user-id <clerk_user_id>
  ./.venv-test/bin/python scripts/semantic_precision_eval.py --user-id <clerk_user_id> --min-delta-pp 1.5 --min-semantic-precision 0.70
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

try:
    from sqlalchemy import select
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "Missing dependency: sqlalchemy. Run with a backend virtualenv, for example:\n"
        "  ./.venv-test/bin/python scripts/semantic_precision_eval.py --user-id <id>"
    ) from exc


def _bootstrap_api_gateway_imports() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    api_gateway_dir = repo_root / "backend" / "api_gateway"
    sys.path.insert(0, str(api_gateway_dir))


_bootstrap_api_gateway_imports()

from models.job import Job  # noqa: E402
from models.resume import Resume  # noqa: E402
from models.application import Application  # noqa: E402
from models.approval import Approval  # noqa: E402
from db.session import SessionLocal  # noqa: E402
from services.semantic_match_service import (  # noqa: E402
    SemanticMatcherUnavailableError,
    semantic_fit_score,
)


def _precision(predicted_positive: int, true_positive: int) -> float | None:
    if predicted_positive == 0:
        return None
    return true_positive / predicted_positive


def _as_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _template_label(job: Job, threshold: float) -> bool:
    template = job.score_template if isinstance(job.score_template, dict) else {}
    baseline_score = _as_float(template.get("fit_score"), 3.0)
    return baseline_score >= threshold


def _outcome_label(app_statuses: list[str], approval_statuses: list[str], sent_count: int) -> bool:
    positive_app_status = {"applied", "interview", "offer"}
    positive_approval_status = {"approved", "edited"}
    return (
        any(s in positive_app_status for s in app_statuses)
        or sent_count > 0
        or any(s in positive_approval_status for s in approval_statuses)
    )


async def _run_eval(
    user_id: str,
    sample_size: int,
    label_threshold: float,
    blend_weight: float,
    label_mode: str,
    min_delta_pp: float | None,
    min_semantic_precision: float | None,
) -> int:
    async with SessionLocal() as session:
        latest_resume = (
            await session.execute(
                select(Resume)
                .where(Resume.user_id == user_id)
                .order_by(Resume.created_at.desc(), Resume.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest_resume is None:
            print(f"error: no resume found for user_id={user_id}")
            return 1

        jobs = (
            await session.execute(
                select(Job)
                .where(Job.score_template.is_not(None))
                .order_by(Job.discovered_at.desc())
                .limit(sample_size)
            )
        ).scalars().all()
        if not jobs:
            print("error: no catalog jobs with score_template found")
            return 1

        app_rows = (
            await session.execute(
                select(Application.job_id, Application.status)
                .where(Application.user_id == user_id)
                .where(Application.job_id.in_([j.id for j in jobs]))
            )
        ).all()
        approvals_rows = (
            await session.execute(
                select(Application.job_id, Approval.status, Approval.sent_at)
                .join(Approval, Approval.application_id == Application.id)
                .where(Application.user_id == user_id)
                .where(Application.job_id.in_([j.id for j in jobs]))
            )
        ).all()

        apps_by_job: dict[str, list[str]] = {}
        for job_id, status in app_rows:
            apps_by_job.setdefault(job_id, []).append(str(status))

        approvals_by_job: dict[str, list[str]] = {}
        sent_by_job: dict[str, int] = {}
        for job_id, status, sent_at in approvals_rows:
            approvals_by_job.setdefault(job_id, []).append(str(status))
            if sent_at is not None:
                sent_by_job[job_id] = sent_by_job.get(job_id, 0) + 1

        parsed_profile = latest_resume.parsed_profile
        blend_weight = max(0.0, min(1.0, blend_weight))
        effective_label_mode = label_mode
        if label_mode == "auto":
            outcome_labeled_jobs = sum(
                1
                for job in jobs
                if apps_by_job.get(job.id) or approvals_by_job.get(job.id) or sent_by_job.get(job.id, 0) > 0
            )
            # Require at least 20% coverage to avoid noisy metrics on tiny outcome samples.
            effective_label_mode = "outcome" if outcome_labeled_jobs >= max(3, int(len(jobs) * 0.2)) else "template"

        baseline_pred_pos = 0
        baseline_true_pos = 0
        blend_pred_pos = 0
        blend_true_pos = 0
        semantic_applied = 0

        for job in jobs:
            template = job.score_template if isinstance(job.score_template, dict) else {}
            baseline_score = _as_float(template.get("fit_score"), 3.0)
            if effective_label_mode == "outcome":
                label_relevant = _outcome_label(
                    app_statuses=apps_by_job.get(job.id, []),
                    approval_statuses=approvals_by_job.get(job.id, []),
                    sent_count=sent_by_job.get(job.id, 0),
                )
            else:
                label_relevant = _template_label(job, label_threshold)

            baseline_pred = baseline_score >= label_threshold
            if baseline_pred:
                baseline_pred_pos += 1
                if label_relevant:
                    baseline_true_pos += 1

            semantic_score = None
            try:
                semantic_score = semantic_fit_score(parsed_profile, job)
            except SemanticMatcherUnavailableError:
                print("error: sentence-transformers unavailable; install it in your backend env")
                return 1

            blended_score = baseline_score
            if semantic_score is not None:
                semantic_applied += 1
                blended_score = ((1.0 - blend_weight) * baseline_score) + (blend_weight * semantic_score)

            blend_pred = blended_score >= label_threshold
            if blend_pred:
                blend_pred_pos += 1
                if label_relevant:
                    blend_true_pos += 1

        baseline_precision = _precision(baseline_pred_pos, baseline_true_pos)
        blend_precision = _precision(blend_pred_pos, blend_true_pos)

        print("Doubow Semantic Precision Eval (Offline)")
        print("---------------------------------------")
        print(f"user_id: {user_id}")
        print(f"sample_size: {len(jobs)}")
        print(f"label_threshold: {label_threshold:.1f}")
        print(f"blend_weight: {blend_weight:.2f}")
        print(f"label_mode_requested: {label_mode}")
        print(f"label_mode_effective: {effective_label_mode}")
        print(f"semantic_scored_jobs: {semantic_applied}")
        print("")
        if effective_label_mode == "outcome":
            print(
                "ground_truth_proxy: relevant := app/approval outcomes "
                "(applied/interview/offer OR approved/edited OR sent approval)"
            )
        else:
            print(
                "ground_truth_proxy: relevant := job.score_template.fit_score >= threshold "
                "(replace with human labels when available)"
            )
        print("")
        print(
            "baseline_precision: "
            + (f"{baseline_precision:.2%}" if baseline_precision is not None else "n/a (no predicted positives)")
        )
        print(
            "semantic_blend_precision: "
            + (f"{blend_precision:.2%}" if blend_precision is not None else "n/a (no predicted positives)")
        )
        if baseline_precision is not None and blend_precision is not None:
            delta_pp = (blend_precision - baseline_precision) * 100
            print(f"delta_precision_pp: {delta_pp:+.2f}")
        else:
            delta_pp = None
            print("delta_precision_pp: n/a")

        # Optional quality gates for automated CI-style checks.
        gate_failures: list[str] = []
        if min_delta_pp is not None:
            if delta_pp is None:
                gate_failures.append("min_delta_pp gate could not be evaluated (missing precision values)")
            elif delta_pp < min_delta_pp:
                gate_failures.append(
                    f"delta_precision_pp {delta_pp:+.2f} < required {min_delta_pp:+.2f}"
                )
        if min_semantic_precision is not None:
            if blend_precision is None:
                gate_failures.append(
                    "min_semantic_precision gate could not be evaluated (no semantic predicted positives)"
                )
            elif blend_precision < min_semantic_precision:
                gate_failures.append(
                    f"semantic_blend_precision {blend_precision:.2%} < required {min_semantic_precision:.2%}"
                )

        if min_delta_pp is not None or min_semantic_precision is not None:
            print("")
            print("quality_gates:")
            if gate_failures:
                for failure in gate_failures:
                    print(f"- FAIL: {failure}")
                return 2
            print("- PASS")

        return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare baseline vs semantic-blend precision on catalog jobs.")
    parser.add_argument("--user-id", required=True, help="User id to source latest parsed resume profile")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of latest catalog jobs to evaluate")
    parser.add_argument("--threshold", type=float, default=4.0, help="Decision threshold for predicted positive fit")
    parser.add_argument("--blend-weight", type=float, default=0.25, help="Semantic blend weight in [0,1]")
    parser.add_argument(
        "--label-mode",
        choices=("auto", "template", "outcome"),
        default="auto",
        help="Label source for relevance (default: auto)",
    )
    parser.add_argument(
        "--min-delta-pp",
        type=float,
        default=None,
        help="Optional gate: require semantic precision uplift (percentage points) >= this value.",
    )
    parser.add_argument(
        "--min-semantic-precision",
        type=float,
        default=None,
        help="Optional gate: require semantic blend precision >= this ratio (0..1).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(
        asyncio.run(
            _run_eval(
                user_id=args.user_id,
                sample_size=max(1, args.sample_size),
                label_threshold=args.threshold,
                blend_weight=args.blend_weight,
                label_mode=args.label_mode,
                min_delta_pp=args.min_delta_pp,
                min_semantic_precision=args.min_semantic_precision,
            )
        )
    )
