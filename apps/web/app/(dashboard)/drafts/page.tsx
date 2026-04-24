import { Suspense } from 'react'
import ApprovalsPage from '@/src/approvals/page'

export default function DraftsRoutePage() {
  return (
    <Suspense fallback={null}>
      <ApprovalsPage />
    </Suspense>
  )
}
