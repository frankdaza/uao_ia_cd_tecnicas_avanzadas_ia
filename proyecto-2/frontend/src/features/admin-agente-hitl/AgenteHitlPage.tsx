import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { ApiError, fetchAgenteHitlConfig, patchAgenteHitlConfig } from '@/lib/api'
import { formatFechaAlta } from '@/lib/formatFecha'

/** Configuracion HITL en escalamiento clinico (solo administrador). */
export function AgenteHitlPage() {
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['admin', 'agente-hitl'],
    queryFn: fetchAgenteHitlConfig,
  })

  const [habilitado, setHabilitado] = useState(false)

  useEffect(() => {
    if (q.data) {
      setHabilitado(q.data.habilitado)
    }
  }, [q.data])

  const guardar = useMutation({
    mutationFn: () => patchAgenteHitlConfig({ habilitado }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['admin', 'agente-hitl'] })
      toast.success('Configuracion de escalamiento guardada.')
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

  const dirty = q.data != null && habilitado !== q.data.habilitado

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
          Escalamiento clinico (HITL)
        </h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Controla si el agente exige aprobacion del personal antes de persistir alertas de triage
          urgentes. El cambio aplica a nuevos mensajes de pacientes sin reiniciar el servidor.
        </p>
      </div>

      {q.isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Cargando configuracion…</p>
      ) : null}

      {q.isError ? (
        <p className="text-sm text-[var(--destructive)]">
          {q.error instanceof ApiError
            ? (q.error.detail ?? q.error.message)
            : 'No se pudo cargar la configuracion HITL.'}
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
              id="agente-hitl-habilitado"
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-[var(--color-border)]"
              checked={habilitado}
              onChange={(e) => setHabilitado(e.target.checked)}
            />
            <div>
              <Label htmlFor="agente-hitl-habilitado" className="font-medium">
                Exigir aprobacion staff (HITL)
              </Label>
              <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                <strong className="font-medium text-[var(--color-text)]">Desactivado</strong>{' '}
                (recomendado en demo): las alertas urgentes o de seguimiento aparecen de inmediato en
                la bandeja de alertas.
              </p>
              <p className="mt-2 text-sm text-[var(--color-text-muted)]">
                <strong className="font-medium text-[var(--color-text)]">Activado</strong>: la tool{' '}
                <code className="text-xs">escalar_a_equipo</code> queda pendiente de aprobacion; el
                paciente recibe un mensaje generico y la bandeja permanece vacia hasta que un
                administrador reanude el hilo vía API staff.
              </p>
            </div>
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
