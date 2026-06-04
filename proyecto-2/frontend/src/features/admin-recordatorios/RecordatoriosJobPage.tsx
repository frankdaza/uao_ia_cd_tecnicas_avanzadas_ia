import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, fetchRecordatoriosJobConfig, patchRecordatoriosJobConfig } from '@/lib/api'
import { formatFechaAlta } from '@/lib/formatFecha'

/** Configuracion del job periodico de recordatorios (solo administrador). */
export function RecordatoriosJobPage() {
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['admin', 'recordatorios-job'],
    queryFn: fetchRecordatoriosJobConfig,
  })

  const [habilitado, setHabilitado] = useState(false)
  const [intervalSeg, setIntervalSeg] = useState('60')

  useEffect(() => {
    if (q.data) {
      setHabilitado(q.data.habilitado)
      setIntervalSeg(String(q.data.interval_seg))
    }
  }, [q.data])

  const guardar = useMutation({
    mutationFn: () => {
      const parsed = Number.parseInt(intervalSeg, 10)
      if (!Number.isFinite(parsed) || parsed < 5 || parsed > 3600) {
        return Promise.reject(new Error('El intervalo debe estar entre 5 y 3600 segundos.'))
      }
      return patchRecordatoriosJobConfig({
        habilitado,
        interval_seg: parsed,
      })
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['admin', 'recordatorios-job'] })
      toast.success('Configuracion de recordatorios guardada.')
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : err instanceof Error
            ? err.message
            : 'No se pudo guardar la configuracion.'
      toast.error(msg)
    },
  })

  const dirty =
    q.data != null &&
    (habilitado !== q.data.habilitado || intervalSeg !== String(q.data.interval_seg))

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
          Recordatorios programados
        </h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Controla el envio automatico de recordatorios de medicacion, terapia y control por Telegram
          en casos con chat vinculado (no semilla ficticia).
        </p>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          El <strong className="font-medium text-[var(--color-text)]">intervalo en segundos</strong>{' '}
          define cada cuanto el job revisa la cola y el espaciado entre plantillas del mismo caso: 1.º
          medicacion a N s, 2.º terapia a 2N s, 3.º control a 3N s tras crear el caso (o al guardar un
          nuevo intervalo, se reprograman los pendientes). Ejemplo con N=10: envios aprox. a los 10, 20
          y 30 segundos. La fecha de cirugia del caso es solo informativa en el panel.
        </p>
      </div>

      {q.isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Cargando configuracion…</p>
      ) : null}

      {q.isError ? (
        <p className="text-sm text-[var(--destructive)]">
          {q.error instanceof ApiError
            ? (q.error.detail ?? q.error.message)
            : 'No se pudo cargar la configuracion del job.'}
        </p>
      ) : null}

      {q.data ? (
        <form
          className="space-y-6 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6"
          onSubmit={(e) => {
            e.preventDefault()
            guardar.mutate()
          }}
        >
          <div className="flex items-start gap-3">
            <input
              id="recordatorios-job-habilitado"
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-[var(--color-border)]"
              checked={habilitado}
              onChange={(e) => setHabilitado(e.target.checked)}
            />
            <div>
              <Label htmlFor="recordatorios-job-habilitado" className="font-medium">
                Job activo
              </Label>
              <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                Si esta desactivado, no se enviaran recordatorios automaticos hasta volver a
                activarlo (sin reiniciar el servidor).
              </p>
            </div>
          </div>

          <div className="space-y-2 max-w-xs">
            <Label htmlFor="recordatorios-job-intervalo">Intervalo entre recordatorios (segundos)</Label>
            <Input
              id="recordatorios-job-intervalo"
              type="number"
              min={5}
              max={3600}
              value={intervalSeg}
              onChange={(e) => setIntervalSeg(e.target.value)}
            />
            <p className="text-xs text-[var(--color-text-subtle)]">
              Entre 5 y 3600. El job ejecuta un ciclo cada N segundos y envia los pendientes cuyo
              horario ya vencio. Si no hay Telegram real vinculado, revise logs (omitidos o
              pendientes=0).
            </p>
          </div>

          {q.data.updated_at ? (
            <p className="text-xs text-[var(--color-text-subtle)]">
              Ultima actualizacion: {formatFechaAlta(q.data.updated_at)}
            </p>
          ) : null}

          <div className="flex gap-2">
            <Button type="submit" disabled={!dirty || guardar.isPending}>
              {guardar.isPending ? 'Guardando…' : 'Guardar cambios'}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={!dirty || guardar.isPending}
              onClick={() => {
                if (q.data) {
                  setHabilitado(q.data.habilitado)
                  setIntervalSeg(String(q.data.interval_seg))
                }
              }}
            >
              Descartar
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  )
}
