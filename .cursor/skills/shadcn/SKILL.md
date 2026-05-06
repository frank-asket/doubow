---
name: shadcn
description: >-
  Build and extend UI using shadcn/ui conventions in the Doubow web app—Radix
  primitives, Tailwind, cn(), accessible patterns, and composable Card/Button-style
  structure. Use when adding components, forms, dialogs, or refactoring crowded pages
  toward consistent, token-driven surfaces.
---

# shadcn-style UI (Doubow)

This repo targets **Next.js + Tailwind + Radix** patterns aligned with [shadcn/ui](https://ui.shadcn.com/) even when a component was hand-rolled.

## When this skill applies

- New buttons, inputs, cards, dialogs, dropdowns, or layout shells in `apps/web`
- Replacing ad-hoc class strings with composable, accessible primitives
- Reducing visual noise: one primary action per region, clear hierarchy, consistent radii

## Project facts

- **Merge classes**: `cn()` from `@/lib/utils` (`clsx` + `tailwind-merge`).
- **Radix**: `@radix-ui/react-dialog`, `dropdown-menu`, `select`, `tooltip`, `progress` are already dependencies—prefer them for behavior, style with Tailwind.
- **Tokens**: Brand and surfaces live in `apps/web/app/globals.css` (`:root`, `.app-route-shell`, `--color-primary-green`, etc.). Prefer CSS variables and existing Tailwind theme keys over one-off hex when extending.
- **No full shadcn CLI tree yet**: Add components via `npx shadcn@latest add <component>` when you need the official file; then adapt imports to `@/components/ui/...` and keep using `cn()`.

## Implementation rules

1. **Structure**: Mirror shadcn composition—small presentational building blocks, variants via `className` + `cn()`, not giant JSX blobs.
2. **Accessibility**: Visible focus rings (`focus-visible:ring-*`), correct `aria-*` on Radix triggers, keyboard support from primitives.
3. **Motion**: Prefer specific `transition-*` utilities; avoid `transition-all` unless every property must animate.
4. **Density**: Follow “one hero idea per block”—if a section has competing chips, links, and badges, merge into a single secondary line or move extras to the next section (UI/UX clarity).

## Related skills

- **Anthropic `frontend-design`**: Distinctive, intentional aesthetics—avoid generic “AI slop” while staying on-brand (greens, editorial display type).
- **ui-ux-pro-max** (optional install): Stack-specific palettes and patterns—cross-check suggestions against Doubow tokens.
- **runkids/skillshare**: Sync this and other skills to Cursor/Claude/etc.; run `skillshare sync` from your configured source.
