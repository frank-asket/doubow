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
| Technical Depth | 20% | Problem selection and scope |  |  |
| Technical Depth | 20% | Architecture and design choices |  |  |
| Technical Depth | 20% | Prompt/model interaction quality |  |  |
| Technical Depth | 20% | Orchestration and control flow |  |  |
| Engineering Practices | 20% | Code quality |  |  |
| Engineering Practices | 20% | Logging and error handling |  |  |
| Engineering Practices | 20% | Unit/integration testing |  |  |
| Engineering Practices | 20% | Observability |  |  |
| Production Readiness | 15% | Solution feasibility |  |  |
| Production Readiness | 15% | Evaluation strategy |  |  |
| Production Readiness | 15% | Deployment readiness |  |  |
| Presentation | 15% | User interface quality |  |  |
| Presentation | 15% | Demo quality |  |  |
| Presentation | 15% | Communication clarity |  |  |

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
- Key risks:
- Must-fix before production:
- Recommended next step:
