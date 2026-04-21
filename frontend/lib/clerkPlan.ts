/**
 * Mirrors optional fields written by Clerk Billing / backend webhooks into
 * `publicMetadata` (see frontend/middleware.ts paywall helpers).
 */
export type ClerkPlanPublicMetadata = {
  plan?: string
  subscriptionStatus?: string
  /** e.g. pro_monthly, business_yearly — common from Clerk Billing webhooks */
  planTier?: string
  stripePriceId?: string
  stripe_price_id?: string
}

/**
 * Optional JSON map of Stripe price IDs to sidebar labels, e.g.
 * NEXT_PUBLIC_PLAN_PRICE_LABELS={"price_abc123":"Pro","price_def456":"Business"}
 */
function priceIdLabelMap(): Record<string, string> {
  if (typeof process.env.NEXT_PUBLIC_PLAN_PRICE_LABELS !== 'string') return {}
  try {
    const parsed = JSON.parse(process.env.NEXT_PUBLIC_PLAN_PRICE_LABELS) as unknown
    if (!parsed || typeof parsed !== 'object') return {}
    const out: Record<string, string> = {}
    for (const [k, v] of Object.entries(parsed)) {
      if (typeof k === 'string' && typeof v === 'string' && k && v) out[k] = v
    }
    return out
  } catch {
    return {}
  }
}

function labelFromTierSegment(segment: string): string | null {
  const s = segment.trim().toLowerCase()
  if (s === 'free') return 'Free'
  if (s === 'pro') return 'Pro'
  if (s === 'business') return 'Business'
  if (s === 'enterprise') return 'Enterprise'
  return null
}

/** Maps planTier strings like pro_monthly → Pro */
function labelFromPlanTier(raw: string): string {
  const normalized = raw.trim().toLowerCase().replace(/-/g, '_')
  const firstSegment = normalized.split('_')[0] ?? normalized
  const mapped = labelFromTierSegment(firstSegment)
  if (mapped) return mapped
  return firstSegment.charAt(0).toUpperCase() + firstSegment.slice(1).toLowerCase()
}

export function planLabelFromPublicMetadata(
  meta: ClerkPlanPublicMetadata | null | undefined,
): string {
  if (!meta) return 'Free'

  const priceKey = meta.stripePriceId ?? meta.stripe_price_id
  if (typeof priceKey === 'string' && priceKey.trim()) {
    const mapped = priceIdLabelMap()[priceKey.trim()]
    if (mapped) return mapped
  }

  const tierRaw = typeof meta.planTier === 'string' ? meta.planTier.trim() : ''
  if (tierRaw) return labelFromPlanTier(tierRaw)

  const rawPlan = typeof meta.plan === 'string' ? meta.plan.trim().toLowerCase() : ''
  if (rawPlan === 'free') return 'Free'
  if (rawPlan === 'pro') return 'Pro'
  if (rawPlan === 'business') return 'Business'
  if (rawPlan.length > 0) {
    return rawPlan.charAt(0).toUpperCase() + rawPlan.slice(1)
  }
  if (meta.subscriptionStatus === 'active') return 'Active'
  return 'Free'
}

/** Used by middleware to treat planTier like plan for paid checks */
export function isPaidPublicMetadata(meta: ClerkPlanPublicMetadata | undefined): boolean {
  if (!meta) return false
  if (meta.subscriptionStatus === 'active') return true
  const rawPlan = typeof meta.plan === 'string' ? meta.plan.trim().toLowerCase() : ''
  if (rawPlan && rawPlan !== 'free') return true
  const tier = typeof meta.planTier === 'string' ? meta.planTier.trim().toLowerCase() : ''
  if (tier) {
    const seg = tier.split(/[_-]/)[0] ?? tier
    if (seg !== 'free') return true
  }
  return false
}
