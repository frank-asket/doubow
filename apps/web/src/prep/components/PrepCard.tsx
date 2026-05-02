export function PrepCard({ title, questions }: { title: string; questions: string[] }) {
  return (
    <div className="card p-4 bg-bg-light-orange border border-border-subtle">
      <p className="text-sm font-medium text-primary-orange">{title}</p>
      <ul className="mt-2 list-disc pl-4 text-xs text-text-muted">
        {questions.map((question) => (
          <li key={question}>{question}</li>
        ))}
      </ul>
    </div>
  )
}
