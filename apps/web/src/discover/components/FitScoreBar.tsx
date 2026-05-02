export function FitScoreBar({ score }: { score: number }) {
  return (
    <div className="h-1 w-full rounded bg-bg-light-green">
      <div className="h-1 rounded bg-primary-green" style={{ width: `${Math.max(0, Math.min(100, score * 20))}%` }} />
    </div>
  )
}
