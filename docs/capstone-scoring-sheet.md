# Q1 Capstone Scoring Sheet

Use this sheet to evaluate capstone submissions consistently across reviewers.

## Scoring Scale (1-5)

- `1` = Not demonstrated / major gaps
- `2` = Emerging but incomplete
- `3` = Meets baseline expectations
- `4` = Strong and reliable
- `5` = Excellent, production-grade, clearly above baseline

## Weighted Criteria

Rate each criterion from 1-5, then multiply by its weight.

| Category | Weight | Criteria | Score (1-5) | Weighted Score |
|---|---:|---|---:|---:|
| Technical Depth | 20% | Problem selection and scope | 4.5 |  |
| Technical Depth | 20% | Architecture and design choices | 4.5 |  |
| Technical Depth | 20% | Prompt/model interaction quality | 3.5 |  |
| Technical Depth | 20% | Orchestration and control flow | 4.0 |  |
| Engineering Practices | 20% | Code quality | 4.0 |  |
| Engineering Practices | 20% | Logging and error handling | 4.0 |  |
| Engineering Practices | 20% | Unit/integration testing | 4.0 |  |
| Engineering Practices | 20% | Observability | 3.5 |  |
| Production Readiness | 15% | Solution feasibility | 4.0 |  |
| Production Readiness | 15% | Evaluation strategy | 3.0 |  |
| Production Readiness | 15% | Deployment readiness | 3.5 |  |
| Presentation | 15% | User interface quality | 4.5 |  |
| Presentation | 15% | Demo quality | 3.5 |  |
| Presentation | 15% | Communication clarity | 4.0 |  |

## Category Scoring Formula

For each category:

`Category Score (0-100) = (Average criterion score / 5) * 100`

`Weighted Category Contribution = Category Score * Category Weight`

Overall score:

`Final Score (0-100) = Sum of all weighted category contributions`

## Quick Calculator Layout

Copy this into your notes/spreadsheet:

- Technical Depth avg: `____ / 5` -> contribution: `____ * 0.20`
- Engineering Practices avg: `____ / 5` -> contribution: `____ * 0.20`
- Production Readiness avg: `____ / 5` -> contribution: `____ * 0.15`
- Presentation avg: `____ / 5` -> contribution: `____ * 0.15`
- **Final Score**: `____ / 100`

Draft filled values:

- Technical Depth avg: `4.13 / 5` -> contribution: `82.5 * 0.20 = 16.5`
- Engineering Practices avg: `3.88 / 5` -> contribution: `77.5 * 0.20 = 15.5`
- Production Readiness avg: `3.50 / 5` -> contribution: `70.0 * 0.15 = 10.5`
- Presentation avg: `4.00 / 5` -> contribution: `80.0 * 0.15 = 12.0`
- **Weighted subtotal (per rubric weights listed): `54.5 / 70`**
- **Normalized final score: `77.9 / 100`**

## Rating Anchors by Category

### Technical Depth
- `1-2`: unclear scope, weak architecture rationale, brittle prompting
- `3`: clear scope, sensible architecture, acceptable prompt behavior
- `4-5`: strong decomposition, robust orchestration, thoughtful model controls

### Engineering Practices
- `1-2`: inconsistent code quality, minimal tests, weak failure handling
- `3`: readable code, baseline tests, reasonable logging and errors
- `4-5`: clean structure, meaningful test coverage, strong diagnostics and observability

### Production Readiness
- `1-2`: prototype only, little feasibility evidence, no deployment path
- `3`: realistic feasibility, basic evaluation, plausible deployment plan
- `4-5`: clear rollout strategy, rigorous evaluation, operational confidence

### Presentation
- `1-2`: unclear narrative, fragile demo, weak stakeholder communication
- `3`: understandable story and functional demo
- `4-5`: concise narrative, strong live demo, confident communication of trade-offs

## Reviewer Notes

- Key strengths:
  - Clear AI engineering scope with realistic product workflow (discover, scoring, approvals, prep).
  - Solid architecture decomposition (Next.js frontend, FastAPI API gateway, Clerk auth, Postgres + Redis).
  - Strong safety posture improvements: user-scoped tenancy, typed error envelopes, idempotency checks, integration tests.
  - Dashboard UX quality significantly improved with cross-breakpoint visual regression coverage.
- Key risks:
  - Evaluation strategy for LLM quality is still light (limited quantitative quality benchmarks and acceptance gates).
  - Observability is good for events but not yet full production ops (alerts, SLOs, tracing depth).
  - Deployment hardening and rollback playbooks need tighter explicit documentation.
- Must-fix before production:
  - Add formal eval suite for prompt/model outputs (quality rubric + pass/fail thresholds).
  - Define and document SLOs, alert conditions, and incident-response basics.
  - Validate production auth/RLS posture end-to-end with non-superuser data access guarantees.
- Recommended next step:
  - Ship a `docs/capstone-readiness.md` package containing: eval metrics dashboard, deployment checklist, demo script, and final risk register.
