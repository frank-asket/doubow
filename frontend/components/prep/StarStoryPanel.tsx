import type { StarStory } from '@/types'

export function StarStoryPanel({ stories }: { stories: StarStory[] }) {
  return <div className="card p-4 text-xs text-surface-600">{stories.length} STAR-R stories</div>
}
