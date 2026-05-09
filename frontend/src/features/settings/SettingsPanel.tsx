import { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { useSettings } from './SettingsContext'
import { useModels } from '@/hooks/useModels'
import { useReloadCorpus } from '@/hooks/useReloadCorpus'
import { useSalud } from '@/hooks/useSalud'
import { getPromptDefecto } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

/** Panel lateral de configuración de modelos, contexto y prompt del sistema. */
export function SettingsPanel() {
  const { settings, updateSettings } = useSettings()
  const { data: modelos, isLoading: cargandoModelos } = useModels()
  const { data: salud } = useSalud()
  const recargar = useReloadCorpus()
  const [promptEditado, setPromptEditado] = useState<string | null>(null)

  const apiOnline = salud?.estado === 'ok'

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
      {/* Estado de la API */}
      <div className="flex items-center justify-between">
        <span className="font-semibold text-[var(--color-text-muted)]">Estado de la API</span>
        <Badge variant={apiOnline ? 'success' : 'destructive'}>
          {apiOnline ? 'En línea' : 'Sin conexión'}
        </Badge>
      </div>

      <Separator />

      {/* Motor Ollama */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <label htmlFor="toggle-ollama" className="font-medium">
            Usar Ollama
          </label>
          <Switch
            id="toggle-ollama"
            checked={settings.usarOllama}
            onCheckedChange={(v) => updateSettings({ usarOllama: v })}
            aria-label="Activar motor Ollama"
          />
        </div>

        {settings.usarOllama && (
          <div className="flex flex-col gap-2 pl-1">
            {cargandoModelos ? (
              <Skeleton className="h-9 w-full" />
            ) : (
              <Select
                value={settings.modeloOllama}
                onValueChange={(v) => updateSettings({ modeloOllama: v })}
              >
                <SelectTrigger aria-label="Modelo Ollama">
                  <SelectValue placeholder="Selecciona un modelo" />
                </SelectTrigger>
                <SelectContent>
                  {modelos?.modelos_ollama.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            <div className="flex flex-col gap-1">
              <div className="flex justify-between text-xs text-[var(--color-text-muted)]">
                <span>Ventana de contexto</span>
                <span>{settings.numCtx.toLocaleString()} tokens</span>
              </div>
              <Slider
                min={4096}
                max={16384}
                step={2048}
                value={[settings.numCtx]}
                onValueChange={([v]) => updateSettings({ numCtx: v })}
                aria-label="Ventana de contexto Ollama"
              />
            </div>
          </div>
        )}
      </div>

      <Separator />

      {/* Motor OpenAI */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <label htmlFor="toggle-openai" className="font-medium">
            Usar OpenAI
          </label>
          {modelos?.openai_disponible ? (
            <Switch
              id="toggle-openai"
              checked={settings.usarOpenai}
              onCheckedChange={(v) => updateSettings({ usarOpenai: v })}
              aria-label="Activar motor OpenAI"
            />
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <div>
                  <Switch
                    id="toggle-openai"
                    checked={false}
                    disabled
                    aria-label="Motor OpenAI no disponible (sin API key)"
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent>Sin clave OPENAI_API_KEY configurada</TooltipContent>
            </Tooltip>
          )}
        </div>

        {settings.usarOpenai && modelos?.openai_disponible && (
          <div className="flex flex-col gap-2 pl-1">
            {cargandoModelos ? (
              <Skeleton className="h-9 w-full" />
            ) : (
              <Select
                value={settings.modeloOpenai}
                onValueChange={(v) => updateSettings({ modeloOpenai: v })}
              >
                <SelectTrigger aria-label="Modelo OpenAI">
                  <SelectValue placeholder="Selecciona un modelo" />
                </SelectTrigger>
                <SelectContent>
                  {modelos?.modelos_openai.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        )}
      </div>

      <Separator />

      {/* Prompt del sistema */}
      <Accordion type="single" collapsible>
        <AccordionItem value="prompt">
          <AccordionTrigger className="text-sm font-medium">
            Prompt del sistema
          </AccordionTrigger>
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

      {/* Acciones del corpus */}
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
