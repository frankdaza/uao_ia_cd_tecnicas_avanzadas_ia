/** Vista placeholder de listado de casos (TASK posteriores). */
export function PlaceholderCasos() {
  return (
    <section className="max-w-2xl space-y-4">
      <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">Casos</h2>
      <p className="text-sm text-[var(--color-text-muted)]">
        Aquí irá el listado y detalle de casos posoperatorios conectado a{' '}
        <code className="text-xs bg-[var(--color-surface-2)] px-1 py-0.5 rounded">/api/staff/casos</code>.
      </p>
    </section>
  )
}
