# Doubow DESIGN.md

Design direction for Doubow (Supabase-first dark aesthetic with Linear-style density and hierarchy).

## 1) Visual Theme & Atmosphere

- Dark-first, operator-grade product feel.
- Crisp, minimal surfaces with subtle separation lines.
- High information clarity; low decorative noise.
- Confident green accent used for action and status.

## 2) Color Palette & Roles

- `--background`: `#000000` (page background)
- `--foreground`: `#fafafa` (primary text)
- `--card`: `#0a0a0a` (primary surface)
- `--surface-2`: `#111113` (secondary controls/surfaces)
- `--border`: `#27272a` (dividers/borders)
- `--muted`: `#a1a1aa` (secondary text)
- `--mint`: `#4ade80` (primary action)
- `--mint-bright`: `#34d399` (primary hover/active)
- `--cyan`: `#22d3ee` (secondary accent/info)

## 3) Typography Rules

- Sans-serif interface typography, high readability over style novelty.
- Tight heading rhythm, compact body spacing.
- Preferred hierarchy:
  - H1: bold, high contrast, compact line-height
  - H2/H3: strong but restrained
  - Body: concise and scannable
  - Meta text: subdued with muted color

## 4) Component Stylings

- Buttons:
  - Default: dark surface with border
  - Primary: mint fill with black text
  - Hover: subtle lightening for dark buttons, brighter mint for primary
- Inputs:
  - Dark card surface, muted placeholder, mint focus ring
- Cards:
  - Card background + subtle border + minimal shadow
- Dividers:
  - Consistent `--border`, avoid heavy outlines

## 5) Layout Principles

- Container max width around 1100–1140px for marketing pages.
- Prioritize vertical rhythm through compact section spacing.
- Use dense but breathable blocks for tables/cards.
- Prefer clear sectional grouping over ornamental structure.

## 6) Do / Don't

Do:
- Keep copy concise and product-specific.
- Use mint accent intentionally for CTAs and key states.
- Favor real product structure over template motifs.

Don't:
- Use bright decorative gradients as primary UI style.
- Overuse shadows, rounded corners, or oversized spacing.
- Mix many accent colors in one section.

## 7) Responsive Behavior

- Preserve hierarchy first, then reduce spacing.
- Maintain readable line-lengths on mobile.
- Keep CTAs reachable without visual clutter.

## 8) Agent Prompt Guide

When generating UI in Doubow:
- Use dark base surfaces with mint accents.
- Prefer dense, clear, production-like information layouts.
- Keep structure modular and component-driven.
- Avoid “template landing” styling patterns.

## 9) Monochrome Style Guard (PR Gate)

Current visual policy is strict monochrome: black, white, and gray only.

Do not introduce color utility classes outside the zinc/neutral/black/white scale.

Disallowed utility prefixes (Tailwind examples):
- `emerald-*`, `green-*`, `lime-*`
- `amber-*`, `yellow-*`, `orange-*`
- `sky-*`, `blue-*`, `cyan-*`, `teal-*`
- `violet-*`, `purple-*`, `indigo-*`, `pink-*`
- `rose-*`, `red-*`

Allowed:
- `black`, `white`, `zinc-*`, `neutral-*`, `gray-*` (when needed)

Pre-PR check (run from repo root):

```bash
rg "emerald|amber|sky|violet|rose|cyan|lime|teal|indigo|blue-|purple|green-|red-|orange-|yellow-|pink-" frontend --glob "*.{ts,tsx,css}"
```

If this command returns matches, the PR is not monochrome-compliant and must be fixed before merge.
