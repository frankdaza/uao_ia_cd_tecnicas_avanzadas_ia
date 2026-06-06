import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, BellRing, Loader2, MessageSquareOff } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  ApiError,
  dispararRecordatorioPrueba,
  getStaffCasoResumen,
  getStaffConversacion,
  listStaffAlertas,
  markAlertaRevisada,
} from '@/lib/api'
import { formatFechaAlta } from '@/lib/formatFecha'
import type { AlertaTriage } from '@/lib/schemas'
import { AlertaCard } from './AlertaCard'
import { ListaAdjuntosMensaje } from './AdjuntoMensajeVista'
import { ConversacionHilo } from './ConversacionHilo'
import { SeveridadBadge } from './SeveridadBadge'
import { SEGUIMIENTO_PATH } from './seguimientoPaths'

interface CasoSeguimientoDetallePageProps {
  casoId: string
  onNavigate: (path: string) => void
}

/** Detalle de caso: resumen, conversación y marcar alertas revisadas. */
export function CasoSeguimientoDetallePage({ casoId, onNavigate }: CasoSeguimientoDetallePageProps) {
  const qc = useQueryClient()

  const resumenQ = useQuery({
    queryKey: ['staff', 'resumen', casoId],
    queryFn: () => getStaffCasoResumen(casoId),
  })

  const conversacionQ = useQuery({
    queryKey: ['staff', 'conversacion', casoId],
    queryFn: () => getStaffConversacion(casoId),
    retry: (count, err) => {
      if (err instanceof ApiError && err.status === 404) return false
      return count < 1
    },
  })

  const alertasCasoQ = useQuery({
    queryKey: ['staff', 'alertas', 'caso', casoId],
    queryFn: () => listStaffAlertas({ revisado: false, caso_id: casoId, limit: 20 }),
  })

  const recordatorioPruebaMut = useMutation({
    mutationFn: () => dispararRecordatorioPrueba(casoId),
    onSuccess: (data) => {
      if (data.enviado) {
        toast.success('Recordatorio enviado por Telegram.')
      } else {
        const detalle = data.mensaje ?? data.motivo_omitido ?? 'No se pudo enviar.'
        toast.warning(detalle)
      }
      void qc.invalidateQueries({ queryKey: ['staff', 'resumen', casoId] })
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : 'No se pudo disparar el recordatorio de prueba.'
      toast.error(msg)
    },
  })

  const marcarMut = useMutation({
    mutationFn: (alerta: AlertaTriage) => markAlertaRevisada(alerta.id),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['staff', 'alertas'] })
      await qc.invalidateQueries({ queryKey: ['staff', 'resumen', casoId] })
      toast.success('Alerta marcada como revisada.')
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : 'No se pudo marcar la alerta.'
      toast.error(msg)
    },
  })

  const sinTelegram =
    conversacionQ.error instanceof ApiError && conversacionQ.error.status === 404

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Button type="button" variant="ghost" size="sm" onClick={() => onNavigate(SEGUIMIENTO_PATH)}>
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Volver a bandeja
      </Button>

      {resumenQ.isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Cargando resumen…</p>
      ) : null}

      {resumenQ.data ? (
        <section className="rounded-lg border border-[var(--border)] p-4 space-y-2">
          <h2 className="font-display text-lg font-semibold text-[var(--color-text)]">
            Resumen del caso
          </h2>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-[var(--color-text-subtle)]">Telegram</dt>
              <dd className="text-[var(--color-text)]">
                {resumenQ.data.vinculado_telegram
                  ? `Vinculado (${resumenQ.data.telegram_chat_id_enmascarado ?? 'chat'})`
                  : 'Sin vínculo activo'}
              </dd>
            </div>
            <div>
              <dt className="text-[var(--color-text-subtle)]">Mensajes en hilo</dt>
              <dd className="text-[var(--color-text)]">{resumenQ.data.conteo_mensajes}</dd>
            </div>
            {resumenQ.data.ultima_severidad ? (
              <div className="sm:col-span-2">
                <dt className="text-[var(--color-text-subtle)] mb-1">Última alerta</dt>
                <dd className="flex flex-wrap items-center gap-2">
                  <SeveridadBadge severidad={resumenQ.data.ultima_severidad} />
                  <span className="text-[var(--color-text)]">
                    {resumenQ.data.ultima_alerta_resumen}
                  </span>
                  {resumenQ.data.ultima_alerta_created_at ? (
                    <time className="text-xs text-[var(--color-text-subtle)]">
                      {formatFechaAlta(resumenQ.data.ultima_alerta_created_at)}
                    </time>
                  ) : null}
                </dd>
                {resumenQ.data.ultima_alerta_adjuntos.length > 0 ? (
                  <dd className="mt-2 sm:col-span-2">
                    <ListaAdjuntosMensaje
                      adjuntos={resumenQ.data.ultima_alerta_adjuntos}
                      compacto
                    />
                  </dd>
                ) : null}
              </div>
            ) : null}
            {resumenQ.data.proximo_recordatorio_at ? (
              <div className="sm:col-span-2">
                <dt className="text-[var(--color-text-subtle)]">Próximo recordatorio</dt>
                <dd className="text-[var(--color-text)]">
                  {formatFechaAlta(resumenQ.data.proximo_recordatorio_at)}
                  {resumenQ.data.proximo_recordatorio_estado
                    ? ` (${resumenQ.data.proximo_recordatorio_estado})`
                    : ''}
                </dd>
              </div>
            ) : null}
          </dl>
          <div className="pt-2 border-t border-[var(--border)]">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={
                !resumenQ.data.vinculado_telegram || recordatorioPruebaMut.isPending
              }
              title={
                resumenQ.data.vinculado_telegram
                  ? 'Envía el siguiente recordatorio pendiente sin esperar la fecha programada'
                  : 'Empareje Telegram antes de enviar un recordatorio de prueba'
              }
              onClick={() => recordatorioPruebaMut.mutate()}
            >
              {recordatorioPruebaMut.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              ) : (
                <BellRing className="h-4 w-4 shrink-0" aria-hidden />
              )}
              {recordatorioPruebaMut.isPending ? 'Enviando…' : 'Enviar recordatorio de prueba'}
            </Button>
            <p className="mt-2 text-xs text-[var(--color-text-muted)]">
              No sustituye al job automático: solo dispara el siguiente pendiente para validar
              Telegram. Los envíos programados usan el intervalo del panel admin (medicación, terapia
              y control espaciados N, 2N y 3N segundos desde el alta del caso).
            </p>
          </div>
        </section>
      ) : null}

      {alertasCasoQ.data && alertasCasoQ.data.items.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-text-subtle)]">
            Alertas pendientes de este caso
          </h3>
          <ul className="space-y-3">
            {alertasCasoQ.data.items.map((alerta) => (
              <li key={alerta.id}>
                <AlertaCard
                  alerta={alerta}
                  onNavigate={onNavigate}
                  onMarcarRevisado={(a) => marcarMut.mutate(a)}
                  marcando={marcarMut.isPending && marcarMut.variables?.id === alerta.id}
                />
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--color-text-subtle)]">
            Conversación paciente–bot
          </h3>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled
            title="Fuera del MVP: no se responde al paciente desde el panel. Use el bot en Telegram."
          >
            Responder en Telegram
          </Button>
        </div>
        <p className="text-xs text-[var(--color-text-muted)]">
          Solo lectura. La respuesta al paciente se realiza únicamente por el bot en Telegram (fuera
          de este panel en MVP).
        </p>

        {conversacionQ.isLoading ? (
          <p className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            Cargando conversación…
          </p>
        ) : null}

        {sinTelegram ? (
          <div className="flex items-start gap-3 rounded-lg border border-dashed border-[var(--border)] p-6 text-sm text-[var(--color-text-muted)]">
            <MessageSquareOff className="h-5 w-5 shrink-0 text-[var(--color-text-subtle)]" aria-hidden />
            <p>
              {conversacionQ.error instanceof ApiError
                ? (conversacionQ.error.detail ?? conversacionQ.error.message)
                : 'Este caso no tiene vínculo Telegram activo; no hay conversación que mostrar.'}
            </p>
          </div>
        ) : null}

        {conversacionQ.data ? <ConversacionHilo mensajes={conversacionQ.data.mensajes} /> : null}
      </section>
    </div>
  )
}
