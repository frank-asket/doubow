# Daubo Design System

This file is the text-source version of the design system and implementation guidance.
It translates product design decisions into shippable UI behavior.

## Core Principle

Every visual decision serves the human-in-the-loop contract:
- users can scan quickly,
- drill into context when needed,
- and feel safe approving or rejecting AI work.

## Semantic Color Contract

Use color for meaning only, not decoration:
- Teal: trust, success, system healthy
- Amber: attention required, pending review, queue state
- Red: rejection, stop, destructive action
- Blue: email channel and email-origin artifacts
- Purple: LinkedIn channel and interview-related artifacts

If status can be misread without reading text, the design fails.

## Surface and Border Hierarchy

Flat surfaces are intentional for dense scanning:
- Sidebar is the only persistent non-white surface.
- Content surfaces are white with 0.5px borders.
- Border opacity defines hierarchy:
  - Tertiary: default separation
  - Secondary: hover and lightweight emphasis
  - Primary: hard separation and focus grouping

Do not introduce elevation as a hierarchy shortcut.

## Typography Rules

- Weight 400: informational body content.
- Weight 500: headings, labels, actionable values.
- Avoid heavier weights to prevent false urgency in embedded contexts.

## Fit Score Explanation Pattern

Do not collapse fit into a single opaque number.
Always show the 5 scoring dimensions:
- Tech
- Culture
- Seniority
- Comp
- Location

Represent each as a bar so users can inspect tradeoffs before approval.

## Approval Card Contract

The approval card structure is fixed across channels:
1. Company logo
2. Role title
3. Channel badge
4. Subject line
5. Draft preview (truncated on purpose)
6. HITL notice with shield icon
7. Action row

Action constraints:
- Reject is always visible.
- Reject is always red.
- Reject is never hidden or disabled.

---

## Best Immediate Move: First-Session Activation

This is the first implementation priority because it drives activation and trust.

### Scope

Implement two coordinated experiences:
1. Discover empty state (before first resume upload)
2. Onboarding success state after upload ("scoring in progress" with ETA)

### 1) Discover Empty State (No Resume Yet)

**Trigger**
- User has no resume on file.

**Page behavior**
- Replace generic empty message with task-oriented starter state.
- Disable or hide job cards list container.
- Show a single primary CTA to upload resume.

**Content spec**
- Title: `No jobs yet — upload your resume to start matching.`
- Body: `Daubo scores your fit across tech, culture, seniority, comp, and location before showing jobs.`
- Primary CTA: `Upload Resume`
- Secondary link: `How matching works`

**Visual spec**
- Empty state appears in the main Discover pane, not a modal.
- Keep white surface + tertiary border, no shadow.
- Use one amber info badge: `No resume connected`.

### 2) Onboarding Success: Scoring in Progress

**Trigger**
- Resume upload succeeds and parsing starts.

**Page behavior**
- Immediately transition to progress state in Discover.
- Show explicit processing status with ETA.
- Poll status until first scored jobs are available.

**Status blocks**
- `Upload complete`
- `Parsing resume`
- `Scoring job matches`
- `Building your first queue`

Exactly one block is active at a time.

**Content spec**
- Title: `Great — your resume is uploaded.`
- Body: `We are scoring your first set of jobs now. This usually takes about 1-2 minutes.`
- Status label: `Scoring in progress`
- ETA chip: `~2 min`
- Optional helper line: `You can leave this page. We will keep processing in the background.`

### Completion State: First Jobs Ready

**Trigger**
- First scored jobs available in catalog.

**Behavior**
- Replace progress state with populated Discover list.
- Show transient success toast:
  - `Your first matches are ready.`
- Auto-focus top job card.

---

## Engineering Acceptance Criteria

- Discover empty state renders when resume count is zero.
- Upload success transitions to progress state in under 300ms.
- Progress UI exposes current step and ETA placeholder.
- Progress survives refresh via backend status endpoint.
- First-jobs-ready transition happens automatically without manual refresh.
- Reject action on approval cards remains visible in all onboarding-related states.

## Telemetry (Required)

Track these events:
- `discover_empty_viewed`
- `resume_upload_started`
- `resume_upload_succeeded`
- `match_scoring_started`
- `match_scoring_eta_shown`
- `first_matches_ready`

Primary KPI:
- time from `resume_upload_succeeded` to `first_matches_ready`.

## Out of Scope (Next Pass)

- Mobile nav conversion (sidebar to bottom nav)
- Settings and billing IA
- Integration management surface

