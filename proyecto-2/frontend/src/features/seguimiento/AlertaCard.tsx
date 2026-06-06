import { CheckCircle2, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { formatFechaAlta } from '@/lib/formatFecha'
import type { AlertaTriage } from '@/lib/schemas'
import { cn } from '@/lib/cn'
import { casoSeguimientoPath } from './seguimientoPaths'
import { ListaAdjuntosMensaje } from './AdjuntoMensajeVista'
import { SeveridadBadge } from './SeveridadBadge'
import { severidadCardClass } from './severidadStyles'

interface AlertaCardProps {
  alerta: AlertaTriage
  onNavigate: (path: string) => void
  onMarcarRevisado?: (alerta: AlertaTriage) => void
  marcando?: boolean
  showMarcar?: boolean
}

/** Tarjeta de alerta en bandeja o detalle de caso. */
export function AlertaCard({
  alerta,
  onNavigate,
  onMarcarRevisado,
  marcando,
  showMarcar = true,
}: AlertaCardProps) {
  const esUrgente = alerta.severidad === 'urgente'

  return (
    <article
      className={cn(
        'rounded-lg border p-4 transition-shadow',
        severidadCardClass(alerta.severidad),
        esUrgente && 'shadow-sm',
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <SeveridadBadge severidad={alerta.severidad} />
        <time className="text-xs text-[var(--color-text-subtle)]" dateTime={alerta.created_at}>
          {formatFechaAlta(alerta.created_at)}
        </time>
      </div>
      <h3 className="mt-2 font-medium text-[var(--color-text)]">{alerta.paciente_nombre}</h3>
      <p className="text-xs text-[var(--color-text-muted)]">Doc. {alerta.paciente_doc_id}</p>
      <p className="mt-2 text-sm text-[var(--color-text)]">{alerta.resumen}</p>
      {alerta.mensaje_paciente_ref ? (
        <p className="mt-1 text-xs italic text-[var(--color-text-muted)]">
          Ref. paciente: {alerta.mensaje_paciente_ref}
        </p>
      ) : null}
      {alerta.adjuntos.length > 0 ? (
        <ListaAdjuntosMensaje adjuntos={alerta.adjuntos} compacto className="mt-3" />
      ) : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onNavigate(casoSeguimientoPath(alerta.caso_id, alerta.id))}
        >
          <ExternalLink className="h-3 w-3" aria-hidden />
          Ver conversación
        </Button>
        {showMarcar && !alerta.revisado && onMarcarRevisado ? (
          <Button
            type="button"
            size="sm"
            disabled={marcando}
            onClick={() => onMarcarRevisado(alerta)}
          >
            <CheckCircle2 className="h-3 w-3" aria-hidden />
            Marcar revisado
          </Button>
        ) : null}
        {alerta.revisado ? (
          <span className="self-center text-xs text-[var(--color-text-subtle)]">Revisada</span>
        ) : null}
      </div>
    </article>
  )
}
