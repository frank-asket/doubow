export function PrepCard({ title, questions }: { title: string; questions: string[] }) {
  return (
    <div className="card p-4">
      <p className="text-sm font-medium">{title}</p>
      <ul className="mt-2 list-disc pl-4 text-xs text-surface-600">
        {questions.map((question) => (
          <li key={question}>{question}</li>
        ))}
      </ul>
    </div>
  )
}
