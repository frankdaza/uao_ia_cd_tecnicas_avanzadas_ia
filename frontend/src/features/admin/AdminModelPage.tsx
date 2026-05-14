import { useState } from 'react'
import { HelpCircle } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { getAdminConfig, patchAdminConfig } from '@/lib/adminApi'
import type { AdminConfigEstado } from '@/lib/adminSchemas'
import {
  validarHistorialTurnosMax,
  validarIdentificadorModelo,
  validarRagMmrLambda,
  validarRagRerankerModelo,
  validarRagRerankerTopNEntrada,
  validarRagScoreMinimo,
  validarRagTopK,
  validarRagTopKInicial,
  validarTemperatura,
  validarTopP,
} from '@/lib/adminFormValidators'
import { ApiError } from '@/lib/api'

type Props = {
  adminKey: string
}

function EtiquetaConAyudaRag({
  htmlFor,
  etiqueta,
  lineasAyuda,
}: {
  htmlFor: string
  etiqueta: string
  lineasAyuda: readonly string[]
}) {
  return (
    <div className="flex items-center gap-1.5">
      <Label htmlFor={htmlFor}>{etiqueta}</Label>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className="inline-flex rounded-md text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label={`Información: ${etiqueta}`}
          >
            <HelpCircle className="h-4 w-4 shrink-0" aria-hidden />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs text-left font-normal leading-relaxed">
          {lineasAyuda.map((linea, i) => (
            <p key={`${htmlFor}-ayuda-${i}`} className={i > 0 ? 'mt-1.5' : undefined}>
              {linea}
            </p>
          ))}
        </TooltipContent>
      </Tooltip>
    </div>
  )
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
  const [ragTopK, setRagTopK] = useState(String(data.rag_top_k))
  const [ragScoreMinimo, setRagScoreMinimo] = useState(String(data.rag_score_minimo))
  const [ragTopKInicial, setRagTopKInicial] = useState(String(data.rag_top_k_inicial))
  const [ragMmrHabilitado, setRagMmrHabilitado] = useState(data.rag_mmr_habilitado)
  const [ragMmrLambda, setRagMmrLambda] = useState(String(data.rag_mmr_lambda))
  const [ragRerankerHabilitado, setRagRerankerHabilitado] = useState(data.rag_reranker_habilitado)
  const [ragRerankerModelo, setRagRerankerModelo] = useState(data.rag_reranker_modelo)
  const [ragRerankerTopNEntrada, setRagRerankerTopNEntrada] = useState(String(data.rag_reranker_top_n_entrada))
  const [historialTurnosMax, setHistorialTurnosMax] = useState(String(data.historial_turnos_max))
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
    const eRk = validarRagTopK(ragTopK)
    if (eRk) next.ragTopK = eRk
    const eRs = validarRagScoreMinimo(ragScoreMinimo)
    if (eRs) next.ragScoreMinimo = eRs
    const eRki = validarRagTopKInicial(ragTopKInicial)
    if (eRki) next.ragTopKInicial = eRki
    const eRml = validarRagMmrLambda(ragMmrLambda)
    if (eRml) next.ragMmrLambda = eRml
    const eRrm = validarRagRerankerModelo(ragRerankerModelo)
    if (eRrm) next.ragRerankerModelo = eRrm
    const eRtn = validarRagRerankerTopNEntrada(ragRerankerTopNEntrada)
    if (eRtn) next.ragRerankerTopNEntrada = eRtn
    const eHt = validarHistorialTurnosMax(historialTurnosMax)
    if (eHt) next.historialTurnosMax = eHt
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
      rag_top_k: Number.parseInt(ragTopK, 10),
      rag_score_minimo: Number.parseFloat(ragScoreMinimo),
      rag_top_k_inicial: Number.parseInt(ragTopKInicial, 10),
      rag_mmr_habilitado: ragMmrHabilitado,
      rag_mmr_lambda: Number.parseFloat(ragMmrLambda),
      rag_reranker_habilitado: ragRerankerHabilitado,
      rag_reranker_modelo: ragRerankerModelo.trim(),
      rag_reranker_top_n_entrada: Number.parseInt(ragRerankerTopNEntrada, 10),
      historial_turnos_max: Number.parseInt(historialTurnosMax, 10),
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
      <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-4">
        <h2 className="text-sm font-medium text-foreground">Memoria conversacional (compositor)</h2>
        <p className="text-xs text-muted-foreground">
          Cantidad máxima de <strong>turnos</strong> (cada mensaje del usuario cuenta como un turno) que se envían al
          modelo que redacta la respuesta final y al router. Si no hay valor en base de datos, aplica{' '}
          <code className="text-xs">HISTORIAL_TURNOS_MAX</code> del entorno.
        </p>
        <div className="space-y-2 max-w-xs">
          <Label htmlFor="historial-turnos-max">historial_turnos_max</Label>
          <Input
            id="historial-turnos-max"
            type="number"
            min={1}
            max={200}
            step={1}
            value={historialTurnosMax}
            onChange={(e) => setHistorialTurnosMax(e.target.value)}
            aria-invalid={errores.historialTurnosMax ? true : undefined}
            aria-describedby={errores.historialTurnosMax ? 'err-hist-t' : undefined}
          />
          {errores.historialTurnosMax ? (
            <p id="err-hist-t" className="text-sm text-destructive" role="alert">
              {errores.historialTurnosMax}
            </p>
          ) : null}
        </div>
      </div>
      <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-4">
        <h2 className="text-sm font-medium text-foreground">Recuperación RAG (Qdrant)</h2>
        <p className="text-xs text-muted-foreground">
          Parámetros de la herramienta <code className="text-xs">rag_denso</code>. Si la columna correspondiente en
          base de datos está vacía, aplican (en orden) el archivo de configuración, luego las variables de entorno:{' '}
          <code className="text-xs">RAG_TOP_K</code>, <code className="text-xs">RAG_SCORE_MINIMO</code>,{' '}
          <code className="text-xs">RAG_TOP_K_INICIAL</code>, <code className="text-xs">RAG_MMR_HABILITADO</code>,{' '}
          <code className="text-xs">RAG_MMR_LAMBDA</code>, <code className="text-xs">RAG_RERANKER_HABILITADO</code>,{' '}
          <code className="text-xs">RAG_RERANKER_MODELO</code>, <code className="text-xs">RAG_RERANKER_TOP_N_ENTRADA</code>.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <EtiquetaConAyudaRag
              htmlFor="rag-top-k"
              etiqueta="rag_top_k"
              lineasAyuda={[
                'Máximo de fragmentos (chunks) que Qdrant devuelve como candidatos por similitud vectorial. No confundir con el parámetro top_k del modelo de chat: aquí solo afecta a la recuperación RAG.',
                'Ejemplo: 10 permite hasta diez fuentes candidatas antes de filtrar por el umbral de similitud.',
              ]}
            />
            <Input
              id="rag-top-k"
              type="number"
              min={1}
              max={50}
              step={1}
              value={ragTopK}
              onChange={(e) => setRagTopK(e.target.value)}
              aria-invalid={errores.ragTopK ? true : undefined}
              aria-describedby={errores.ragTopK ? 'err-rag-k' : undefined}
            />
            {errores.ragTopK ? (
              <p id="err-rag-k" className="text-sm text-destructive" role="alert">
                {errores.ragTopK}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <EtiquetaConAyudaRag
              htmlFor="rag-score-min"
              etiqueta="rag_score_minimo"
              lineasAyuda={[
                'Puntuación mínima de similitud (0 a 1) para conservar un fragmento en la respuesta de la herramienta. Valores más altos exigen mayor coincidencia con la consulta.',
                'Ejemplo: 0.35 suele descartar coincidencias débiles; 0.5 es más estricto.',
              ]}
            />
            <Input
              id="rag-score-min"
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={ragScoreMinimo}
              onChange={(e) => setRagScoreMinimo(e.target.value)}
              aria-invalid={errores.ragScoreMinimo ? true : undefined}
              aria-describedby={errores.ragScoreMinimo ? 'err-rag-s' : undefined}
            />
            {errores.ragScoreMinimo ? (
              <p id="err-rag-s" className="text-sm text-destructive" role="alert">
                {errores.ragScoreMinimo}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <EtiquetaConAyudaRag
              htmlFor="rag-top-k-inicial"
              etiqueta="rag_top_k_inicial"
              lineasAyuda={[
                'Cantidad de candidatos que Qdrant devuelve antes de aplicar MMR o el reranker (sobrerrecuperación). Debe ser ≥ el top_k final y suele ser mayor para no perder buenos fragmentos tras diversificar o reordenar.',
                'Solo tiene efecto práctico si MMR o el reranker están activos; si ambos están desactivados, el flujo puede acotarse al mismo rag_top_k.',
              ]}
            />
            <Input
              id="rag-top-k-inicial"
              type="number"
              min={1}
              max={200}
              step={1}
              value={ragTopKInicial}
              onChange={(e) => setRagTopKInicial(e.target.value)}
              aria-invalid={errores.ragTopKInicial ? true : undefined}
              aria-describedby={errores.ragTopKInicial ? 'err-rag-ki' : undefined}
            />
            {errores.ragTopKInicial ? (
              <p id="err-rag-ki" className="text-sm text-destructive" role="alert">
                {errores.ragTopKInicial}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <EtiquetaConAyudaRag
              htmlFor="rag-mmr-lambda"
              etiqueta="rag_mmr_lambda"
              lineasAyuda={[
                'En MMR, equilibrio entre relevancia a la consulta (1.0) y diversidad entre fragmentos (0.0). Valores intermedios reducen respuestas con chunks casi duplicados.',
              ]}
            />
            <Input
              id="rag-mmr-lambda"
              type="number"
              min={0}
              max={1}
              step={0.05}
              value={ragMmrLambda}
              onChange={(e) => setRagMmrLambda(e.target.value)}
              aria-invalid={errores.ragMmrLambda ? true : undefined}
              aria-describedby={errores.ragMmrLambda ? 'err-rag-ml' : undefined}
            />
            {errores.ragMmrLambda ? (
              <p id="err-rag-ml" className="text-sm text-destructive" role="alert">
                {errores.ragMmrLambda}
              </p>
            ) : null}
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2 rounded-md border border-border/60 bg-background/50 p-3 sm:col-span-1">
            <div className="flex items-start justify-between gap-3">
              <EtiquetaConAyudaRag
                htmlFor="rag-mmr-on"
                etiqueta="rag_mmr_habilitado"
                lineasAyuda={[
                  'Activa selección MMR (Maximum Marginal Relevance) sobre los candidatos de Qdrant para favorecer fragmentos distintos entre sí, no solo los más parecidos a la pregunta.',
                ]}
              />
              <Switch
                id="rag-mmr-on"
                checked={ragMmrHabilitado}
                onCheckedChange={setRagMmrHabilitado}
                className="mt-0.5 shrink-0"
                aria-label="Activar o desactivar MMR en RAG"
              />
            </div>
          </div>
          <div className="flex flex-col gap-2 rounded-md border border-border/60 bg-background/50 p-3 sm:col-span-1">
            <div className="flex items-start justify-between gap-3">
              <EtiquetaConAyudaRag
                htmlFor="rag-rerank-on"
                etiqueta="rag_reranker_habilitado"
                lineasAyuda={[
                  'Activa un reranker local tipo cross-encoder (p. ej. sentence-transformers) para reordenar los mejores candidatos. Aumenta latencia y uso de CPU o GPU en el servidor; desactivado por defecto en muchos despliegues.',
                ]}
              />
              <Switch
                id="rag-rerank-on"
                checked={ragRerankerHabilitado}
                onCheckedChange={setRagRerankerHabilitado}
                className="mt-0.5 shrink-0"
                aria-label="Activar o desactivar reranker en RAG"
              />
            </div>
          </div>
        </div>
        <div className="space-y-2">
          <EtiquetaConAyudaRag
            htmlFor="rag-rerank-modelo"
            etiqueta="rag_reranker_modelo"
            lineasAyuda={[
              'Identificador del modelo en Hugging Face o ruta local compatible con CrossEncoder (misma familia que BAAI/bge-reranker-base). Debe coincidir con un modelo instalado o descargable en el entorno del backend.',
            ]}
          />
          <Input
            id="rag-rerank-modelo"
            value={ragRerankerModelo}
            onChange={(e) => setRagRerankerModelo(e.target.value)}
            autoComplete="off"
            spellCheck={false}
            className="font-mono text-xs"
            aria-invalid={errores.ragRerankerModelo ? true : undefined}
            aria-describedby={errores.ragRerankerModelo ? 'err-rag-rm' : undefined}
          />
          {errores.ragRerankerModelo ? (
            <p id="err-rag-rm" className="text-sm text-destructive" role="alert">
              {errores.ragRerankerModelo}
            </p>
          ) : null}
        </div>
        <div className="space-y-2 max-w-xs">
          <EtiquetaConAyudaRag
            htmlFor="rag-rerank-top-n"
            etiqueta="rag_reranker_top_n_entrada"
            lineasAyuda={[
              'Techo de fragmentos que pasan al reranker después de MMR (o por orden de similitud si MMR está desactivado). Valores mayores mejoran cobertura del reranker pero aumentan coste.',
            ]}
          />
          <Input
            id="rag-rerank-top-n"
            type="number"
            min={1}
            max={50}
            step={1}
            value={ragRerankerTopNEntrada}
            onChange={(e) => setRagRerankerTopNEntrada(e.target.value)}
            aria-invalid={errores.ragRerankerTopNEntrada ? true : undefined}
            aria-describedby={errores.ragRerankerTopNEntrada ? 'err-rag-rtn' : undefined}
          />
          {errores.ragRerankerTopNEntrada ? (
            <p id="err-rag-rtn" className="text-sm text-destructive" role="alert">
              {errores.ragRerankerTopNEntrada}
            </p>
          ) : null}
        </div>
      </div>
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
