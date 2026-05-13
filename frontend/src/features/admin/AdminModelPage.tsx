import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { getAdminConfig, patchAdminConfig } from '@/lib/adminApi'
import type { AdminConfigEstado } from '@/lib/adminSchemas'
import {
  validarIdentificadorModelo,
  validarTemperatura,
  validarTopP,
} from '@/lib/adminFormValidators'
import { ApiError } from '@/lib/api'

type Props = {
  adminKey: string
}

export function AdminModelPage({ adminKey }: Props) {
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['admin', 'config', adminKey],
    queryFn: () => getAdminConfig(adminKey),
  })

  const mut = useMutation({
    mutationFn: (body: Record<string, unknown>) => patchAdminConfig(adminKey, body),
    onSuccess: async () => {
      toast.success('Parámetros guardados. Se aplicarán en la siguiente conversación.')
      await qc.invalidateQueries({ queryKey: ['admin', 'config', adminKey] })
      await qc.invalidateQueries({ queryKey: ['admin', 'metricas', adminKey] })
    },
    onError: (err: unknown) => {
      const msg = err instanceof ApiError ? err.detail ?? err.message : 'No se pudo guardar.'
      toast.error(msg)
    },
  })

  if (q.isLoading) return <p className="text-sm text-muted-foreground">Cargando…</p>
  if (q.isError || !q.data) return <p className="text-sm text-destructive">No se pudo cargar la configuración.</p>

  return (
    <AdminModelFormInner
      key={q.data.version}
      data={q.data}
      onGuardar={(body) => mut.mutateAsync(body)}
      pendiente={mut.isPending}
    />
  )
}

function AdminModelFormInner({
  data,
  onGuardar,
  pendiente,
}: {
  data: AdminConfigEstado
  onGuardar: (body: Record<string, unknown>) => Promise<unknown>
  pendiente: boolean
}) {
  const [modeloRouter, setModeloRouter] = useState(data.modelo_llm_router)
  const [modeloCompositor, setModeloCompositor] = useState(data.modelo_llm_compositor)
  const [tempRouter, setTempRouter] = useState(String(data.temperatura_router))
  const [tempComp, setTempComp] = useState(String(data.temperatura_compositor))
  const [topPRouter, setTopPRouter] = useState(data.top_p_router != null ? String(data.top_p_router) : '')
  const [topPComp, setTopPComp] = useState(data.top_p_compositor != null ? String(data.top_p_compositor) : '')
  const [kwargsRouter, setKwargsRouter] = useState(JSON.stringify(data.model_kwargs_router ?? {}, null, 2))
  const [kwargsComp, setKwargsComp] = useState(JSON.stringify(data.model_kwargs_compositor ?? {}, null, 2))
  const [errores, setErrores] = useState<Record<string, string>>({})

  async function guardar() {
    const next: Record<string, string> = {}
    const eMr = validarIdentificadorModelo(modeloRouter)
    if (eMr) next.modeloRouter = eMr
    const eMc = validarIdentificadorModelo(modeloCompositor)
    if (eMc) next.modeloCompositor = eMc
    const eTr = validarTemperatura(tempRouter)
    if (eTr) next.tempRouter = eTr
    const eTc = validarTemperatura(tempComp)
    if (eTc) next.tempComp = eTc
    const eTpr = validarTopP(topPRouter, true)
    if (eTpr) next.topPRouter = eTpr
    const eTpc = validarTopP(topPComp, true)
    if (eTpc) next.topPComp = eTpc
    setErrores(next)
    if (Object.keys(next).length > 0) {
      toast.error('Revise los campos marcados antes de guardar.')
      return
    }

    let mkR: Record<string, unknown>
    let mkC: Record<string, unknown>
    try {
      mkR = JSON.parse(kwargsRouter || '{}') as Record<string, unknown>
      mkC = JSON.parse(kwargsComp || '{}') as Record<string, unknown>
    } catch {
      toast.error('JSON inválido en model_kwargs.')
      return
    }
    setErrores({})
    const body: Record<string, unknown> = {
      version: data.version,
      modelo_llm_router: modeloRouter.trim(),
      modelo_llm_compositor: modeloCompositor.trim(),
      temperatura_router: Number.parseFloat(tempRouter),
      temperatura_compositor: Number.parseFloat(tempComp),
      model_kwargs_router: mkR,
      model_kwargs_compositor: mkC,
    }
    if (topPRouter.trim() !== '') body.top_p_router = Number.parseFloat(topPRouter)
    if (topPComp.trim() !== '') body.top_p_compositor = Number.parseFloat(topPComp)
    await onGuardar(body)
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <p className="text-sm text-muted-foreground">
        Temperaturas entre 0 y 2; top_p entre 0 y 1. Parámetros extra del proveedor (p. ej.{' '}
        <code className="text-xs">top_k</code>) van en <code className="text-xs">model_kwargs</code> si el backend
        del modelo los admite.
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="m-router">Modelo router</Label>
          <Input
            id="m-router"
            value={modeloRouter}
            onChange={(e) => setModeloRouter(e.target.value)}
            aria-invalid={errores.modeloRouter ? true : undefined}
            aria-describedby={errores.modeloRouter ? 'err-m-router' : undefined}
          />
          {errores.modeloRouter ? (
            <p id="err-m-router" className="text-sm text-destructive" role="alert">
              {errores.modeloRouter}
            </p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="m-compositor">Modelo compositor</Label>
          <Input
            id="m-compositor"
            value={modeloCompositor}
            onChange={(e) => setModeloCompositor(e.target.value)}
            aria-invalid={errores.modeloCompositor ? true : undefined}
            aria-describedby={errores.modeloCompositor ? 'err-m-compositor' : undefined}
          />
          {errores.modeloCompositor ? (
            <p id="err-m-compositor" className="text-sm text-destructive" role="alert">
              {errores.modeloCompositor}
            </p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="t-router">Temperatura router</Label>
          <Input
            id="t-router"
            type="number"
            step="0.1"
            min={0}
            max={2}
            value={tempRouter}
            onChange={(e) => setTempRouter(e.target.value)}
            aria-invalid={errores.tempRouter ? true : undefined}
            aria-describedby={errores.tempRouter ? 'err-t-router' : undefined}
          />
          {errores.tempRouter ? (
            <p id="err-t-router" className="text-sm text-destructive" role="alert">
              {errores.tempRouter}
            </p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="t-comp">Temperatura compositor</Label>
          <Input
            id="t-comp"
            type="number"
            step="0.1"
            min={0}
            max={2}
            value={tempComp}
            onChange={(e) => setTempComp(e.target.value)}
            aria-invalid={errores.tempComp ? true : undefined}
            aria-describedby={errores.tempComp ? 'err-t-comp' : undefined}
          />
          {errores.tempComp ? (
            <p id="err-t-comp" className="text-sm text-destructive" role="alert">
              {errores.tempComp}
            </p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="tp-r">top_p router (opcional)</Label>
          <Input
            id="tp-r"
            type="number"
            step="0.05"
            min={0}
            max={1}
            value={topPRouter}
            onChange={(e) => setTopPRouter(e.target.value)}
            placeholder="vacío = default API"
            aria-invalid={errores.topPRouter ? true : undefined}
            aria-describedby={errores.topPRouter ? 'err-tp-r' : undefined}
          />
          {errores.topPRouter ? (
            <p id="err-tp-r" className="text-sm text-destructive" role="alert">
              {errores.topPRouter}
            </p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="tp-c">top_p compositor (opcional)</Label>
          <Input
            id="tp-c"
            type="number"
            step="0.05"
            min={0}
            max={1}
            value={topPComp}
            onChange={(e) => setTopPComp(e.target.value)}
            placeholder="vacío = default API"
            aria-invalid={errores.topPComp ? true : undefined}
            aria-describedby={errores.topPComp ? 'err-tp-c' : undefined}
          />
          {errores.topPComp ? (
            <p id="err-tp-c" className="text-sm text-destructive" role="alert">
              {errores.topPComp}
            </p>
          ) : null}
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="kw-r">model_kwargs router (JSON)</Label>
        <Textarea id="kw-r" className="min-h-[120px] font-mono text-xs" value={kwargsRouter} onChange={(e) => setKwargsRouter(e.target.value)} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="kw-c">model_kwargs compositor (JSON)</Label>
        <Textarea id="kw-c" className="min-h-[120px] font-mono text-xs" value={kwargsComp} onChange={(e) => setKwargsComp(e.target.value)} />
      </div>
      <Button
        type="button"
        disabled={pendiente}
        onClick={() => void guardar()}
        aria-label="Guardar parámetros del modelo y sampling"
      >
        Guardar cambios
      </Button>
    </div>
  )
}
