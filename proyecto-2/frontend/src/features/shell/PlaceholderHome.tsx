/** Vista placeholder de inicio del panel staff. */
export function PlaceholderHome() {
  return (
    <section className="max-w-2xl space-y-4">
      <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">Inicio</h2>
      <p className="text-sm text-[var(--color-text-muted)]">
        Bienvenido al panel TAAM (Telegram + API + panel staff). Este es un scaffold sin lógica de
        negocio: use la barra lateral para navegar y el pie de página para comprobar la conexión con
        el backend.
      </p>
    </section>
  )
}
