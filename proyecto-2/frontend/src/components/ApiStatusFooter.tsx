import { useSalud } from '@/hooks/useSalud'

/** Pie de página con estado de la API TAAM (React Query). */
export function ApiStatusFooter() {
  const salud = useSalud()

  const online = salud.data?.estado === 'ok' && salud.data.proyecto === 'taam'
  const ver = salud.data?.version ?? '—'
  const proyecto = salud.data?.proyecto ?? '—'
  const comprobando = salud.isPending || salud.isFetching

  return (
    <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-[10px] text-[var(--color-text-subtle)]">
      <span className="inline-flex items-center gap-1.5">
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            comprobando
              ? 'bg-amber-500'
              : online
                ? 'bg-[var(--color-accent)]'
                : 'bg-red-500'
          }`}
          aria-hidden="true"
        />
        API {comprobando ? 'comprobando…' : online ? 'en línea' : 'desconectada'}
      </span>
      <span>versión backend {ver}</span>
      <span>proyecto {proyecto}</span>
    </div>
  )
}
