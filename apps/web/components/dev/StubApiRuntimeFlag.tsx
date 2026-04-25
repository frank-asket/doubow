/**
 * Sets `window.__DOUBOW_USE_MOCK_API__` from the server on every HTML response.
 * `NEXT_PUBLIC_*` in client bundles is inlined at build time; this keeps stub mode
 * aligned with current Vercel env after you toggle the variable (still redeploy once
 * so this component exists in the bundle).
 */
export default function StubApiRuntimeFlag() {
  const raw = process.env.NEXT_PUBLIC_USE_MOCK_API
  const enabled = raw === 'true' || raw === '1'
  return (
    <script
      // Runs before interactive React; must stay tiny and synchronous.
      dangerouslySetInnerHTML={{
        __html: `try{window.__DOUBOW_USE_MOCK_API__=${enabled};}catch(e){}`,
      }}
    />
  )
}
