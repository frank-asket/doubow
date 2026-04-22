export function DraftPreview({ body }: { body: string }) {
  return <pre className="rounded bg-surface-100 p-3 text-xs whitespace-pre-wrap">{body}</pre>
}
