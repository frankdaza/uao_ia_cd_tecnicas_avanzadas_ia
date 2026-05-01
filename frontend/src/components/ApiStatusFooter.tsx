'use client'

import { useModels } from '@/hooks/useModels'
import { useSalud } from '@/hooks/useSalud'

/** Pie de página con estado de la API y modelos configurados (datos desde React Query). */
export function ApiStatusFooter() {
  const salud = useSalud()
  const modelos = useModels()

  const online = salud.data?.estado === 'ok'
  const ver = salud.data?.version ?? '—'

  return (
    <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-[10px] text-[var(--color-text-subtle)]">
      <span className="inline-flex items-center gap-1.5">
        <span
          className={`inline-block h-2 w-2 rounded-full ${online ? 'bg-emerald-500' : 'bg-red-500'}`}
          aria-hidden="true"
        />
        API {online ? 'en línea' : 'desconectada'}
      </span>
      <span>versión backend {ver}</span>
      {modelos.data && (
        <span>
          OpenAI: {modelos.data.openai_disponible ? 'listo para usar' : 'sin clave API'}
        </span>
      )}
    </div>
  )
}
