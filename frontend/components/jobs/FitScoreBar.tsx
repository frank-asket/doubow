export function FitScoreBar({ score }: { score: number }) {
  return (
    <div className="h-1 w-full rounded bg-surface-100">
      <div className="h-1 rounded bg-brand-400" style={{ width: `${Math.max(0, Math.min(100, score * 20))}%` }} />
    </div>
  )
}
