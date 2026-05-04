import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export type GufCardProps = {
  title: string
  children: ReactNode
  type?: 'green' | 'orange'
  icon?: ReactNode
  className?: string
}

/**
 * Carte style document GUF : fond pastel, titres vert ou orange, rayon 24px.
 * Couleurs : tokens `guf` / variables `--guf-*` dans `globals.css`.
 */
export function GufCard({ title, children, type = 'green', icon, className }: GufCardProps) {
  const surface = type === 'orange' ? 'bg-guf-orange-light' : 'bg-guf-green-light'
  const titleColor = type === 'orange' ? 'text-guf-orange' : 'text-guf-green'

  return (
    <div
      className={cn(
        'relative h-full overflow-hidden rounded-guf border border-black/5 p-8 shadow-sm',
        surface,
        className
      )}
    >
      {icon ? (
        <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white/50">
          {icon}
        </div>
      ) : null}

      <h3 className={cn('mb-4 text-xl font-bold leading-tight', titleColor)}>{title}</h3>

      <div className="text-sm leading-relaxed text-guf-text [&_strong]:font-semibold [&_strong]:text-guf-text">
        {children}
      </div>
    </div>
  )
}

export default GufCard
