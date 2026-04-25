/**
 * Sets `window.__DOUBOW_USE_MOCK_API__` from the server on every HTML response (dev only).
 * In production, `isMockApiEnabled()` ignores mock regardless of build-inlined env.
 */
export default function StubApiRuntimeFlag() {
  if (process.env.NODE_ENV === 'production') {
    return null
  }
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
