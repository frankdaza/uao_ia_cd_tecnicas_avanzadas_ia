import { HelpCircle } from 'lucide-react'
import { useSalud } from '@/hooks/useSalud'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

function EtiquetaConAyuda({ etiqueta, ayuda }: { etiqueta: string; ayuda: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="font-medium">{etiqueta}</span>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] rounded"
            aria-label={`Información: ${etiqueta}`}
          >
            <HelpCircle className="h-3.5 w-3.5" aria-hidden />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs text-xs leading-relaxed">{ayuda}</TooltipContent>
      </Tooltip>
    </div>
  )
}

/** Panel lateral M2: estado del API y modo laboratorio (tema en la barra superior). */
export function SettingsPanel() {
  const { data: salud } = useSalud()

  const apiOnline = salud?.estado === 'ok'
  const mockLlm = salud?.agente_mock_llm === true

  return (
    <div className="flex flex-col gap-4 p-4 text-sm overflow-y-auto h-full border-l border-transparent bg-[color-mix(in_srgb,var(--color-surface)_40%,transparent)]">
      <p className="font-display text-sm font-semibold tracking-tight text-[var(--color-primary)] dark:text-[var(--color-text)]">
        Información del agente
      </p>

      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="font-semibold text-[var(--color-text-muted)]">Estado de la API</span>
        <Badge variant={apiOnline ? 'success' : 'destructive'}>
          {apiOnline ? 'En línea' : 'Sin conexión'}
        </Badge>
      </div>

      {mockLlm && (
        <Badge variant="outline" className="w-fit border-amber-600 text-amber-800 dark:text-amber-300">
          Modo laboratorio (sin OpenAI)
        </Badge>
      )}

      <Separator />

      <div className="flex flex-col gap-2 text-xs text-[var(--color-text-muted)] leading-relaxed">
        <EtiquetaConAyuda
          etiqueta="Arquitectura"
          ayuda="El agente conversacional usa LangGraph como orquestador, herramientas LangChain (FAQ estructurada y RAG denso), vectores en Qdrant y memoria de turnos en PostgreSQL. Los parámetros del modelo se configuran en el servidor."
        />
        <p>
          <span className="font-semibold text-[var(--color-text)]">Agente:</span> LangGraph + RAG denso
          (Qdrant) + FAQ estructurada.
        </p>
        <p>
          <span className="font-semibold text-[var(--color-text)]">Versión backend:</span>{' '}
          {salud?.version ?? '—'}
        </p>
      </div>

      <Separator />

      <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
        Tema claro u oscuro: usa el interruptor en la esquina superior derecha de la pantalla.
      </p>
    </div>
  )
}
