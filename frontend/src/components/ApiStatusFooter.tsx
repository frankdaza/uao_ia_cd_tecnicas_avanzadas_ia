'use client'

import { useSalud } from '@/hooks/useSalud'

/** Pie de página con estado de la API (React Query). */
export function ApiStatusFooter() {
  const salud = useSalud()

  const online = salud.data?.estado === 'ok'
  const ver = salud.data?.version ?? '—'
  const mockLlm = salud.data?.agente_mock_llm === true

  return (
    <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-[10px] text-[var(--color-text-subtle)]">
      <span className="inline-flex items-center gap-1.5">
        <span
          className={`inline-block h-2 w-2 rounded-full ${online ? 'bg-[var(--color-accent)]' : 'bg-red-500'}`}
          aria-hidden="true"
        />
        API {online ? 'en línea' : 'desconectada'}
      </span>
      <span>versión backend {ver}</span>
      {mockLlm && <span>agente: modo laboratorio (sin OpenAI)</span>}
    </div>
  )
}
