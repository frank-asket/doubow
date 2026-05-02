export function DraftPreview({ body }: { body: string }) {
  return <pre className="rounded bg-bg-light-orange p-3 text-xs whitespace-pre-wrap border border-border-subtle text-text-main">{body}</pre>
}
