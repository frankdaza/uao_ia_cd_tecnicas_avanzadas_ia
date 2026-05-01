import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { ThemeToggle } from './ThemeToggle'
import { Button } from './ui/button'
import { Sheet } from '@/components/ui/sheet'
import { ApiStatusFooter } from '@/components/ApiStatusFooter'
import { cn } from '@/lib/cn'

interface AppShellProps {
  sidebar: ReactNode
  children: ReactNode
}

const SIDEBAR_KEY = 'fvl-sidebar-collapsed'
const MAX_ANCHO_MOVIL = 767

/** Layout principal: sidebar en escritorio y sheet deslizable en móvil. */
export function AppShell({ sidebar, children }: AppShellProps) {
  const [esMovil, setEsMovil] = useState(false)
  const [sheetAbierto, setSheetAbierto] = useState(false)
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(SIDEBAR_KEY) === 'true'
    } catch {
      return false
    }
  })

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MAX_ANCHO_MOVIL}px)`)
    const act = () => setEsMovil(mq.matches)
    act()
    mq.addEventListener('change', act)
    return () => mq.removeEventListener('change', act)
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_KEY, String(collapsed))
    } catch {
      //
    }
  }, [collapsed])

  const alternarPanel = useCallback(() => {
    if (esMovil) setSheetAbierto((a) => !a)
    else setCollapsed((c) => !c)
  }, [esMovil])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        document.getElementById('chat-principal-q')?.focus()
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault()
        alternarPanel()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [alternarPanel])

  const muestraAbierto = esMovil ? sheetAbierto : !collapsed

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[var(--color-background)]">
      <header className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--color-surface)_65%,var(--color-background))] shadow-[inset_0_-3px_0_0_var(--color-accent)] z-10 shrink-0 backdrop-blur-[2px]">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={alternarPanel}
            aria-label={
              muestraAbierto
                ? 'Cerrar panel de configuración'
                : 'Abrir panel de configuración'
            }
          >
            {!muestraAbierto ? (
              <PanelLeftOpen className="h-5 w-5" />
            ) : (
              <PanelLeftClose className="h-5 w-5" />
            )}
          </Button>
          <div className="flex flex-col leading-tight">
            <span
              className="font-display font-bold text-sm bg-gradient-to-r from-[var(--color-primary)] via-[var(--color-accent)] to-[var(--color-primary-light)] bg-clip-text text-transparent"
              style={{ WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
            >
              Q&A — Fundación Valle del Lili
            </span>
            <span className="text-[10px] text-[var(--color-text-muted)] hidden sm:block">
              Asistente inteligente · BM25 + Ollama + OpenAI
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggle />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {!esMovil && (
          <aside
            className={cn(
              'border-r border-[var(--border)] bg-[var(--color-surface)] transition-all duration-300 ease-in-out overflow-hidden shrink-0',
              collapsed ? 'w-0' : 'w-72',
            )}
            aria-hidden={collapsed}
            inert={collapsed ? true : undefined}
          >
            <div className="w-72 h-full min-h-0">{sidebar}</div>
          </aside>
        )}

        <main className="flex-1 flex flex-col overflow-hidden">{children}</main>
      </div>

      {esMovil && (
        <Sheet open={sheetAbierto} onOpenChange={setSheetAbierto} title="Configuración" side="left">
          <div className="h-[calc(100dvh-3.25rem)] min-h-0 overflow-hidden">{sidebar}</div>
        </Sheet>
      )}

      <footer className="shrink-0 border-t border-[var(--border)] px-4 py-2 flex flex-col gap-1 bg-[var(--color-background)]">
        <ApiStatusFooter />
        <p className="text-[10px] text-center text-[var(--color-text-subtle)]">
          Técnicas avanzadas de IA — Módulo 1 · Universidad Autónoma de Occidente
        </p>
      </footer>
    </div>
  )
}
