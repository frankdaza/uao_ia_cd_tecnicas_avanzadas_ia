import { type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

type Props = {
  titulo: string
  pathActual: string
  onNavigate: (ruta: string) => void
  onSalirAdmin: () => void
  children: ReactNode
}

const enlaces: { ruta: string; etiqueta: string }[] = [
  { ruta: '/admin', etiqueta: 'Panel' },
  { ruta: '/admin/modelo', etiqueta: 'Modelo y sampling' },
  { ruta: '/admin/prompts', etiqueta: 'Prompts' },
  { ruta: '/admin/usuarios', etiqueta: 'Usuarios' },
]

export function AdminLayout({ titulo, pathActual, onNavigate, onSalirAdmin, children }: Props) {
  return (
    <div className="min-h-svh flex flex-col md:flex-row bg-background">
      <aside className="border-b border-border md:border-b-0 md:border-r md:w-56 shrink-0 bg-card p-4">
        <p className="font-display text-lg font-semibold text-foreground">Admin M2</p>
        <p className="mt-1 text-xs text-muted-foreground">Fundación Valle del Lili</p>
        <Separator className="my-4" />
        <nav className="flex flex-row flex-wrap gap-2 md:flex-col md:gap-1" aria-label="Secciones administrativas">
          {enlaces.map((en) => {
            const activo =
              en.ruta === '/admin'
                ? pathActual === '/admin' || pathActual === '/admin/'
                : pathActual === en.ruta || pathActual.startsWith(`${en.ruta}/`)
            return (
              <Button
                key={en.ruta}
                type="button"
                variant={activo ? 'default' : 'ghost'}
                className="justify-start"
                onClick={() => onNavigate(en.ruta)}
                aria-current={activo ? 'page' : undefined}
              >
                {en.etiqueta}
              </Button>
            )
          })}
        </nav>
        <div className="mt-6 hidden md:block">
          <Button type="button" variant="outline" className="w-full" onClick={onSalirAdmin} aria-label="Salir del panel administrativo">
            Salir del panel
          </Button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-4 md:p-8">
        <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="font-display text-2xl font-semibold text-foreground">{titulo}</h1>
          <div className="md:hidden">
            <Button type="button" variant="outline" size="sm" onClick={onSalirAdmin} aria-label="Salir del panel administrativo">
              Salir
            </Button>
          </div>
        </header>
        {children}
      </main>
    </div>
  )
}
