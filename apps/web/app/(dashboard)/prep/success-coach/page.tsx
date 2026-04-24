import { Suspense } from 'react'
import SuccessCoachPage from '@/src/prep/successCoachPage'

export default function SuccessCoachRoutePage() {
  return (
    <Suspense fallback={null}>
      <SuccessCoachPage />
    </Suspense>
  )
}
