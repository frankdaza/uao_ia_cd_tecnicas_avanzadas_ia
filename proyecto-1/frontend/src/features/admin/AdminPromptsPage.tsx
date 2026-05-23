import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { getAdminConfig, patchAdminConfig } from '@/lib/adminApi'
import type { AdminConfigEstado } from '@/lib/adminSchemas'
import { validarLongitudPromptInstitucional } from '@/lib/adminFormValidators'
import { ApiError } from '@/lib/api'

type Props = {
  adminKey: string
}

export function AdminPromptsPage({ adminKey }: Props) {
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['admin', 'config', adminKey],
    queryFn: () => getAdminConfig(adminKey),
  })

  const mut = useMutation({
    mutationFn: (body: Record<string, unknown>) => patchAdminConfig(adminKey, body),
    onSuccess: async () => {
      toast.success('Prompts guardados.')
      await qc.invalidateQueries({ queryKey: ['admin', 'config', adminKey] })
    },
    onError: (err: unknown) => {
      const msg = err instanceof ApiError ? err.detail ?? err.message : err instanceof Error ? err.message : 'Error'
      toast.error(msg)
    },
  })

  if (q.isLoading) return <p className="text-sm text-muted-foreground">Cargando…</p>
  if (q.isError || !q.data) return <p className="text-sm text-destructive">No se pudo cargar la configuración.</p>

  return (
    <AdminPromptsFormInner
      key={q.data.version}
      data={q.data}
      onGuardar={(body) => mut.mutateAsync(body)}
      pendiente={mut.isPending}
    />
  )
}

function AdminPromptsFormInner({
  data,
  onGuardar,
  pendiente,
}: {
  data: AdminConfigEstado
  onGuardar: (body: Record<string, unknown>) => Promise<unknown>
  pendiente: boolean
}) {
  const [metaTexto, setMetaTexto] = useState(JSON.stringify(data.meta_prompt, null, 2))
  const [institucional, setInstitucional] = useState(data.prompt_institucional)
  const [errorInstitucional, setErrorInstitucional] = useState<string | null>(null)

  async function guardar() {
    setErrorInstitucional(null)
    const errInst = validarLongitudPromptInstitucional(institucional)
    if (errInst) {
      setErrorInstitucional(errInst)
      toast.error(errInst)
      return
    }
    let meta: Record<string, unknown>
    try {
      meta = JSON.parse(metaTexto) as Record<string, unknown>
    } catch {
      toast.error('El meta-prompt no es JSON válido.')
      return
    }
    await onGuardar({
      version: data.version,
      meta_prompt: meta,
      prompt_institucional: institucional,
    })
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-foreground space-y-3">
        <p>
          Al guardar, los textos se persisten en la base de datos y el agente los usa en la{' '}
          <strong>siguiente</strong> pregunta del chat (no hace falta editar archivos en disco ni reiniciar el
          servidor).
        </p>
        <p>
          El <code className="font-mono text-xs">system_prompt</code>, las{' '}
          <code className="font-mono text-xs">reglas_decision</code> y el bloque{' '}
          <code className="font-mono text-xs">herramientas</code> del JSON se envían al modelo del router; las
          descripciones de las tools expuestas al proveedor se alinean a ese mismo JSON. El saludo del compositor
          usa <code className="font-mono text-xs">saludo_template</code> (debe incluir{' '}
          <code className="font-mono text-xs">{'{nombre}'}</code>).
        </p>
        <p>
          El campo <code className="font-mono text-xs">modelo_router</code> dentro del meta-prompt es solo
          referencia documental: el modelo real del router se define en <strong>Modelo y sampling</strong>, en el
          campo <code className="font-mono text-xs">modelo_llm_router</code> o en la variable de entorno
          equivalente.
        </p>
        <p>
          El campo <code className="font-mono text-xs">respuesta_sin_contexto</code> debe ser exactamente{' '}
          <strong>No tengo información suficiente</strong> (política institucional y validación del servidor).
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="meta-json">Meta-prompt del router (JSON validado por el servidor)</Label>
        <Textarea
          id="meta-json"
          className="min-h-[320px] font-mono text-xs"
          value={metaTexto}
          onChange={(e) => setMetaTexto(e.target.value)}
          spellCheck={false}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="prompt-inst">Prompt institucional del compositor</Label>
        <Textarea
          id="prompt-inst"
          className="min-h-[220px] text-sm"
          value={institucional}
          onChange={(e) => {
            setInstitucional(e.target.value)
            setErrorInstitucional(null)
          }}
          aria-invalid={errorInstitucional ? true : undefined}
          aria-describedby={
            [errorInstitucional ? 'err-prompt-inst' : null, 'hint-prompt-inst'].filter(Boolean).join(' ') ||
            undefined
          }
        />
        <p id="hint-prompt-inst" className="text-xs text-muted-foreground">
          Mínimo 80 caracteres (requisito del servidor).
        </p>
        {errorInstitucional ? (
          <p id="err-prompt-inst" className="text-sm text-destructive" role="alert">
            {errorInstitucional}
          </p>
        ) : null}
      </div>
      <Button
        type="button"
        disabled={pendiente}
        onClick={() => void guardar()}
        aria-label="Guardar meta-prompt e institucional"
      >
        Guardar prompts
      </Button>
    </div>
  )
}
