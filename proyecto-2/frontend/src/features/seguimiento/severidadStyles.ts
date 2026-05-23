import type { SeveridadTriage } from '@/lib/schemas'

export const SEVERIDAD_LABEL: Record<SeveridadTriage, string> = {
  info: 'Información',
  seguimiento: 'Seguimiento',
  urgente: 'Urgente',
}

export function severidadCardClass(severidad: SeveridadTriage): string {
  switch (severidad) {
    case 'urgente':
      return 'border-[var(--destructive)]/50 bg-[var(--destructive)]/5 ring-1 ring-[var(--destructive)]/30'
    case 'seguimiento':
      return 'border-amber-500/40 bg-amber-500/5'
    default:
      return 'border-[var(--border)] bg-[var(--color-surface)]/40'
  }
}

export function severidadBadgeClass(severidad: SeveridadTriage): string {
  switch (severidad) {
    case 'urgente':
      return 'bg-[var(--destructive)] text-white'
    case 'seguimiento':
      return 'bg-amber-500/20 text-amber-800 dark:text-amber-200'
    default:
      return 'bg-[var(--color-surface)] text-[var(--color-text-muted)]'
  }
}
