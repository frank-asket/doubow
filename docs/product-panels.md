# Product surface map

Canonical description of each dashboard panel, the intent behind it, and how it fits the agent model. Use this when changing UX, copy, or API contracts so product story and code stay aligned.

## Discover

Discover is where everything starts. Jobs surface after the Discovery agent scans portals and the Scorer agent rates them against your resume. The four stat cards at the top give you the health of your search at a glance — e.g. evaluated vs worth reviewing. Each job card is collapsed by default to reduce noise; click one to expand the 5-dimension score breakdown, the specific reasons it matched, and the risk flags. The **Prepare application** button queues the job — it does not apply yet; it tells the Writer agent to start drafting.

**Route:** `/discover`

## Pipeline

Pipeline is your application tracker. The tab strip filters by status. The integrity banner appears when the Monitor agent has detected duplicates or stale entries — it shows a preview before any change is applied, so you stay in control of what gets cleaned up. The table is intentionally dense because at roughly 7–50 applications you need to scan quickly, not read prose.

**Route:** `/pipeline`

## Approvals

Approvals is the human-in-the-loop gate — the most important panel in the product. Every draft the Writer agent produces lands here in pending state. You see the channel (email vs LinkedIn), the subject line, and the first few lines of the draft. Nothing is sent until you click **Approve & send**. You can also edit the draft inline before approving. The Apply agent is the only agent that can send anything, and it must treat **approved** status as a hard precondition — if that check fails it should raise and stop rather than proceed.

**Route:** `/approvals`

**Implementation guardrail:** sending mail or external apply actions must be enforced in the API (and workers), not only in the UI. The Apply path should verify approval state before any side effect.

## Interview prep

Interview prep is generated per application, not generically. The Prep agent reads the actual JD and your actual resume to produce questions you are specifically likely to face. The STAR-R section gives you a structured story scaffold — Situation, Task, Action, Result, Reflection — populated with your real work so you are not starting from a blank page before an interview.

**Route:** `/prep`

## Resume

Resume is the system’s source of truth. Every other agent draws from the profile extracted here — the scorer uses your skills and archetypes to evaluate fit; the tailor uses your experience history so it cannot invent skills you do not have; the writer draws from your headline and summary for cover letters. The AI analysis extracts your top archetypes and surfaces skill gaps so you know which roles to prioritise.

**Route:** `/resume`

## Agents

Agents gives you visibility into what is running in the background. The Apply agent sitting idle is intentional — it only activates when an approval fires. The Orchestrator chat lets you query your whole pipeline in natural language: ask why a score is low, what to focus on, or for a follow-up draft. It should have full pipeline context injected into every message so answers are specific to your situation, not generic advice.

**Route:** `/agents`
