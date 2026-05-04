export function DraftPreview({ body }: { body: string }) {
  return <pre className="rounded bg-orange-fade p-3 text-xs whitespace-pre-wrap border border-border-subtle text-text-main">{body}</pre>
}
