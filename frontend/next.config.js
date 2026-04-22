const fs = require('fs')
const path = require('path')

/**
 * Next only auto-loads `.env*` from the `frontend/` directory. In this monorepo,
 * secrets often live in the repo root `.env`, so Clerk never sees the publishable key
 * and `<SignIn />` renders blank (no `ClerkProvider`).
 */
function parseEnvFile(contents) {
  const out = {}
  const re =
    /(?:^|^)\s*(?:export\s+)?([\w.-]+)(?:\s*=\s*?|:\s+?)(\s*'(?:\\'|[^'])*'|\s*"(?:\\"|[^"])*"|[^#\r\n]+)?\s*(?:#.*)?(?:$|$)/gm
  let m
  while ((m = re.exec(contents)) !== null) {
    const key = m[1]
    let val = (m[2] ?? '').trim()
    const q = val[0]
    val = val.replace(/^(['"`])([\s\S]*)\1$/gm, '$2')
    if (q === '"') {
      val = val.replace(/\\n/g, '\n').replace(/\\r/g, '\r')
    }
    out[key] = val
  }
  return out
}

function loadEnvFromDir(dir) {
  let merged = {}
  for (const name of ['.env', '.env.local']) {
    const full = path.join(dir, name)
    if (!fs.existsSync(full)) continue
    try {
      merged = { ...merged, ...parseEnvFile(fs.readFileSync(full, 'utf8')) }
    } catch {
      // ignore unreadable env files
    }
  }
  return merged
}

const frontendDir = __dirname
const repoRoot = path.join(frontendDir, '..')
const fromFiles = { ...loadEnvFromDir(repoRoot), ...loadEnvFromDir(frontendDir) }
for (const [key, value] of Object.entries(fromFiles)) {
  if (process.env[key] === undefined) process.env[key] = value
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Exposed so Edge middleware can read the flag after monorepo `.env` merge above.
  env: {
    CLERK_REQUIRE_ACTIVE_SUBSCRIPTION: process.env.CLERK_REQUIRE_ACTIVE_SUBSCRIPTION ?? '',
  },
  // Avoid noisy cross-origin dev warnings during local multi-port flows
  // (e.g. frontend on :3001 and Playwright baseURL on 127.0.0.1:3100).
  allowedDevOrigins: [
    'http://localhost',
    'http://127.0.0.1',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
    'http://localhost:3100',
    'http://127.0.0.1:3100',
    // Playwright / IPv6 localhost (Next cross-origin dev asset checks)
    'http://[::1]:3000',
    'http://[::1]:3100',
  ],
  experimental: {
    typedRoutes: true,
  },
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '*.supabase.co' },
      { protocol: 'https', hostname: 'logo.clearbit.com' },
    ],
  },
}

module.exports = nextConfig
