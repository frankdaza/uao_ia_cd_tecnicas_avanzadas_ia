import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'

interface SettingsPanelProps {
  path: string
  onNavigate: (path: string) => void
  userRol?: string
}

const NAV_ITEMS = [
  { path: '/', label: 'Inicio' },
  { path: '/casos', label: 'Casos' },
  { path: '/seguimiento', label: 'Seguimiento' },
] as const

const NAV_ADMIN = [
  { path: '/admin/procedimientos', label: 'Catálogo procedimientos' },
  { path: '/admin/medicos', label: 'Médicos' },
] as const

/** Barra lateral: navegación placeholder del panel staff. */
export function SettingsPanel({ path, onNavigate, userRol }: SettingsPanelProps) {
  const esAdmin = userRol === 'admin'

  return (
    <nav className="flex flex-col gap-1" aria-label="Navegación principal">
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-subtle)] mb-2">
        Panel TAAM
      </p>
      {NAV_ITEMS.map((item) => {
        const activo = path === item.path || (item.path !== '/' && path.startsWith(item.path))
        return (
          <Button
            key={item.path}
            type="button"
            variant={activo ? 'secondary' : 'ghost'}
            className={cn('justify-start w-full', activo && 'font-semibold')}
            onClick={() => onNavigate(item.path)}
          >
            {item.label}
          </Button>
        )
      })}
      {esAdmin ? (
        <>
          <p className="mt-4 text-xs font-medium uppercase tracking-wide text-[var(--color-text-subtle)] mb-2">
            Administración
          </p>
          {NAV_ADMIN.map((item) => {
            const activo = path === item.path || path.startsWith(`${item.path}/`)
            return (
              <Button
                key={item.path}
                type="button"
                variant={activo ? 'secondary' : 'ghost'}
                className={cn('justify-start w-full', activo && 'font-semibold')}
                onClick={() => onNavigate(item.path)}
              >
                {item.label}
              </Button>
            )
          })}
        </>
      ) : null}
      <p className="mt-6 text-[11px] text-[var(--color-text-subtle)] leading-relaxed">
        Módulo 3 — seguimiento posoperatorio. Registre casos en <strong>Casos</strong>; revise alertas
        y conversaciones en <strong>Seguimiento</strong>.
      </p>
    </nav>
  )
}
