import type { ReactNode } from 'react'
import { ThemeToggle } from './ThemeToggle'
import { ApiStatusFooter } from './ApiStatusFooter'
import { cn } from '@/lib/cn'

interface AppShellProps {
  sidebar: ReactNode
  children: ReactNode
  title?: string
  headerExtras?: ReactNode
}

/** Layout principal del panel staff TAAM (scaffold). */
export function AppShell({ sidebar, children, title = 'TAAM', headerExtras }: AppShellProps) {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[var(--color-background)]">
      <header className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--color-surface)_65%,var(--color-background))] shadow-[inset_0_-3px_0_0_var(--color-accent)] z-10 shrink-0">
        <h1 className="font-display text-lg font-semibold tracking-tight text-[var(--color-text)]">
          {title}
        </h1>
        <div className="flex items-center gap-2">
          {headerExtras}
          <ThemeToggle />
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        <aside
          className={cn(
            'w-64 shrink-0 border-r border-[var(--border)] bg-[var(--color-surface)]',
            'overflow-y-auto p-4 hidden sm:block',
          )}
        >
          {sidebar}
        </aside>
        <main className="flex flex-1 flex-col min-w-0 min-h-0">
          <div className="flex-1 overflow-y-auto p-6">{children}</div>
          <footer className="shrink-0 border-t border-[var(--border)] py-2 px-4 bg-[var(--color-surface)]">
            <ApiStatusFooter />
          </footer>
        </main>
      </div>
    </div>
  )
}
