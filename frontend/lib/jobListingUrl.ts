import type { Job } from '@/types'

const PLACEHOLDER_HOSTS = new Set(['example.com', 'www.example.com'])

/** LinkedIn job search for role + company — useful when seeds only had example.com placeholders. */
function keywordsSearchUrl(job: Pick<Job, 'title' | 'company'>): string {
  const q = encodeURIComponent(`${job.title} ${job.company}`.trim())
  return `https://www.linkedin.com/jobs/search/?keywords=${q}`
}

/**
 * Discover “View JD” uses `job.url`. Catalog migrations historically stored
 * `https://example.com/jobs/...` placeholders — replace those with a real search URL.
 */
export function resolveJobListingUrl(job: Pick<Job, 'url' | 'title' | 'company' | 'source'>): string {
  const raw = job.url?.trim()
  if (!raw) return keywordsSearchUrl(job)

  try {
    const u = new URL(raw)
    if (PLACEHOLDER_HOSTS.has(u.hostname)) {
      return keywordsSearchUrl(job)
    }
    if (job.source === 'catalog' && u.pathname.includes('/jobs/jb_cat_')) {
      return keywordsSearchUrl(job)
    }
  } catch {
    return keywordsSearchUrl(job)
  }

  return raw
}
