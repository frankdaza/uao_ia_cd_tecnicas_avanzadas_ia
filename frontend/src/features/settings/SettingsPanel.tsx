import { useState } from 'react'
import { HelpCircle, RefreshCw } from 'lucide-react'
import { useSettings } from './SettingsContext'
import { useModels } from '@/hooks/useModels'
import { useReloadCorpus } from '@/hooks/useReloadCorpus'
import { useSalud } from '@/hooks/useSalud'
import { getPromptDefecto } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Slider } from '@/components/ui/slider'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

function EtiquetaConAyuda({
  htmlFor,
  etiqueta,
  ayuda,
}: {
  htmlFor: string
  etiqueta: string
  ayuda: string
}) {
  return (
    <div className="flex items-center gap-1.5">
      <label htmlFor={htmlFor} className="font-medium">
        {etiqueta}
      </label>
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

/** Panel lateral de configuración de modelo OpenAI, muestreo y prompt del sistema. */
export function SettingsPanel() {
  const { settings, updateSettings } = useSettings()
  const { data: modelos, isLoading: cargandoModelos } = useModels()
  const { data: salud } = useSalud()
  const recargar = useReloadCorpus()
  const [promptEditado, setPromptEditado] = useState<string | null>(null)

  const apiOnline = salud?.estado === 'ok'
  const openaiDisponible = Boolean(modelos?.openai_disponible)

  const handleRestaurarPrompt = async () => {
    try {
      const pd = await getPromptDefecto()
      setPromptEditado(pd.prompt_sistema)
      updateSettings({ promptSistema: pd.prompt_sistema })
    } catch {
      // silencioso
    }
  }

  return (
    <div className="flex flex-col gap-4 p-4 text-sm overflow-y-auto h-full border-l border-transparent bg-[color-mix(in_srgb,var(--color-surface)_40%,transparent)]">
      <p className="font-display text-sm font-semibold tracking-tight text-[var(--color-primary)] dark:text-[var(--color-text)]">
        Configuración del asistente
      </p>
      <div className="flex items-center justify-between">
        <span className="font-semibold text-[var(--color-text-muted)]">Estado de la API</span>
        <Badge variant={apiOnline ? 'success' : 'destructive'}>
          {apiOnline ? 'En línea' : 'Sin conexión'}
        </Badge>
      </div>

      <Separator />

      <div className="flex flex-col gap-3">
        <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
          Las respuestas se generan con la API de OpenAI. Configura{' '}
          <code className="text-[0.7rem] bg-[var(--color-surface-2)] px-1 rounded">OPENAI_API_KEY</code>{' '}
          en el servidor si aún no está disponible el motor.
        </p>

        {!openaiDisponible && (
          <p className="text-xs text-amber-700 dark:text-amber-400">
            Sin clave de API: el chat no podrá generar respuestas hasta configurar la variable de entorno.
          </p>
        )}

        {cargandoModelos ? (
          <Skeleton className="h-9 w-full" />
        ) : (
          <div className="flex flex-col gap-2">
            <span className="font-medium">Modelo</span>
            <Select
              value={settings.modeloOpenai}
              onValueChange={(v) => updateSettings({ modeloOpenai: v })}
              disabled={!openaiDisponible}
            >
              <SelectTrigger aria-label="Modelo OpenAI">
                <SelectValue placeholder="Selecciona un modelo" />
              </SelectTrigger>
              <SelectContent>
                {(modelos?.modelos_openai ?? []).map((m) => (
                  <SelectItem key={m} value={m}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="flex flex-col gap-2">
          <EtiquetaConAyuda
            htmlFor="slider-temperatura"
            etiqueta="Temperatura"
            ayuda="Controla el azar al elegir el siguiente token. Valores bajos suelen dar respuestas más predecibles y alineadas al contexto; valores altos aumentan la variedad y la creatividad, con más riesgo de divagar."
          />
          <div className="flex justify-between text-xs text-[var(--color-text-muted)] tabular-nums">
            <span />
            <span>{settings.temperatura.toFixed(1)}</span>
          </div>
          <Slider
            id="slider-temperatura"
            min={0}
            max={2}
            step={0.1}
            value={[settings.temperatura]}
            onValueChange={([v]) => updateSettings({ temperatura: v })}
            disabled={!openaiDisponible}
            aria-label="Temperatura de muestreo"
          />
        </div>

        <div className="flex flex-col gap-2">
          <EtiquetaConAyuda
            htmlFor="slider-top-p"
            etiqueta="Top P"
            ayuda="Solo se consideran los tokens más probables hasta alcanzar esta probabilidad acumulada (nucleus sampling). Suele complementar a la temperatura: valores más bajos restringen más el conjunto de candidatos."
          />
          <div className="flex justify-between text-xs text-[var(--color-text-muted)] tabular-nums">
            <span />
            <span>{settings.topP.toFixed(2)}</span>
          </div>
          <Slider
            id="slider-top-p"
            min={0}
            max={1}
            step={0.05}
            value={[settings.topP]}
            onValueChange={([v]) => updateSettings({ topP: v })}
            disabled={!openaiDisponible}
            aria-label="Top P (nucleus sampling)"
          />
        </div>
      </div>

      <Separator />

      <Accordion type="single" collapsible>
        <AccordionItem value="prompt">
          <AccordionTrigger className="text-sm font-medium">Prompt del sistema</AccordionTrigger>
          <AccordionContent>
            <div className="flex flex-col gap-2">
              <Textarea
                rows={6}
                placeholder="Prompt del sistema predeterminado…"
                value={promptEditado ?? settings.promptSistema ?? ''}
                onChange={(e) => {
                  setPromptEditado(e.target.value)
                  updateSettings({ promptSistema: e.target.value || null })
                }}
                aria-label="Prompt del sistema"
                className="resize-none text-xs"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleRestaurarPrompt}
                aria-label="Restaurar prompt predeterminado"
              >
                Restaurar predeterminado
              </Button>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <Separator />

      <div className="flex flex-col gap-2">
        <span className="font-medium">Corpus de documentos</span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => recargar.mutate()}
          disabled={recargar.isPending}
          aria-label="Recargar el índice BM25 del corpus"
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${recargar.isPending ? 'animate-spin' : ''}`} />
          {recargar.isPending ? 'Recargando…' : 'Recargar corpus'}
        </Button>
      </div>
    </div>
  )
}
