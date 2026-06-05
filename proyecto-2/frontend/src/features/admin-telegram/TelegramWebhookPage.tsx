import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  fetchTelegramWebhookEstado,
  registrarTelegramWebhook,
} from '@/lib/api'

const RUTA_WEBHOOK = '/api/integracion/telegram/webhook'
const PLACEHOLDER_URL = `https://tu-tunel.example${RUTA_WEBHOOK}`

function formatearError(err: unknown): string {
  if (err instanceof ApiError) {
    return err.detail ?? err.message
  }
  if (err instanceof Error) {
    return err.message
  }
  return 'No se pudo completar la operacion.'
}

/** Registro del webhook de Telegram hacia la API TAAM (solo administrador). */
export function TelegramWebhookPage() {
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['admin', 'telegram-webhook'],
    queryFn: fetchTelegramWebhookEstado,
  })

  const [url, setUrl] = useState('')
  const [dropPending, setDropPending] = useState(false)

  useEffect(() => {
    if (q.data?.url) {
      setUrl(q.data.url)
    }
  }, [q.data?.url])

  const registrar = useMutation({
    mutationFn: () => {
      const normalizada = url.trim()
      if (!normalizada) {
        return Promise.reject(new Error('Ingrese la URL publica HTTPS del webhook.'))
      }
      return registrarTelegramWebhook({
        url: normalizada,
        drop_pending_updates: dropPending,
      })
    },
    onSuccess: async (data) => {
      setUrl(data.url)
      await qc.invalidateQueries({ queryKey: ['admin', 'telegram-webhook'] })
      toast.success('Webhook registrado en Telegram.')
    },
    onError: (err: unknown) => {
      toast.error(formatearError(err))
    },
  })

  const urlRegistrada = q.data?.url?.trim() ?? ''
  const dirty = url.trim() !== urlRegistrada

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
          Webhook Telegram
        </h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Registre la URL publica HTTPS donde Telegram enviara los updates del bot. Debe apuntar a
          este backend en la ruta canónica{' '}
          <code className="text-xs">{RUTA_WEBHOOK}</code>.
        </p>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          En desarrollo use un tunel (ngrok, Cloudflare Tunnel, etc.). El servidor debe tener{' '}
          <code className="text-xs">TELEGRAM_BOT_TOKEN</code> y{' '}
          <code className="text-xs">TELEGRAM_WEBHOOK_SECRET</code> en su archivo{' '}
          <code className="text-xs">.env</code>; esos valores no se editan desde esta pantalla.
        </p>
      </div>

      {q.isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Consultando estado en Telegram…</p>
      ) : null}

      {q.isError ? (
        <p className="text-sm text-[var(--destructive)]">{formatearError(q.error)}</p>
      ) : null}

      {q.data ? (
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 space-y-4">
          <div className="text-sm">
            <p className="font-medium text-[var(--color-text)]">Estado en Telegram</p>
            <ul className="mt-2 space-y-1 text-[var(--color-text-muted)]">
              <li>
                Webhook:{' '}
                {q.data.configurado ? (
                  <span className="text-[var(--color-text)]">{q.data.url}</span>
                ) : (
                  <span className="italic">sin registrar</span>
                )}
              </li>
              <li>Updates pendientes: {q.data.pending_update_count}</li>
              {q.data.last_error_message ? (
                <li className="text-[var(--destructive)]">
                  Ultimo error: {q.data.last_error_message}
                  {q.data.last_error_date != null
                    ? ` (timestamp ${q.data.last_error_date})`
                    : null}
                </li>
              ) : null}
            </ul>
          </div>
        </div>
      ) : null}

      <form
        className="space-y-6 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6"
        onSubmit={(e) => {
          e.preventDefault()
          registrar.mutate()
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="telegram-webhook-url">URL del webhook</Label>
          <Input
            id="telegram-webhook-url"
            type="url"
            autoComplete="off"
            placeholder={PLACEHOLDER_URL}
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <p className="text-xs text-[var(--color-text-subtle)]">
            Ejemplo: <code className="text-[10px]">{PLACEHOLDER_URL}</code>
          </p>
        </div>

        <div className="flex items-start gap-3">
          <input
            id="telegram-webhook-drop-pending"
            type="checkbox"
            className="mt-1 h-4 w-4 rounded border-[var(--color-border)]"
            checked={dropPending}
            onChange={(e) => setDropPending(e.target.checked)}
          />
          <div>
            <Label htmlFor="telegram-webhook-drop-pending" className="font-medium">
              Descartar updates pendientes
            </Label>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">
              Equivale a <code className="text-[10px]">drop_pending_updates=true</code> en
              setWebhook (util al cambiar de URL de tunel).
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button type="submit" disabled={!url.trim() || registrar.isPending}>
            {registrar.isPending ? 'Registrando…' : 'Registrar webhook'}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={!dirty || registrar.isPending}
            onClick={() => {
              if (q.data?.url) {
                setUrl(q.data.url)
              } else {
                setUrl('')
              }
              setDropPending(false)
            }}
          >
            Descartar cambios
          </Button>
        </div>
      </form>
    </div>
  )
}
