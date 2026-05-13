import { ThemeProvider } from 'next-themes'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { SettingsProvider } from '@/features/settings/SettingsContext'
import { AuthProvider, useAuth } from '@/features/auth/AuthContext'
import { AuthScreen } from '@/features/auth/AuthScreen'
import { AppShell } from '@/components/AppShell'
import { SettingsPanel } from '@/features/settings/SettingsPanel'
import { Chat } from '@/features/chat/Chat'
import { Button } from '@/components/ui/button'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

function AppAutenticada() {
  const { usuario, cerrarSesion } = useAuth()

  const headerExtras =
    usuario != null ? (
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] max-w-[min(200px,40vw)]">
        <span className="truncate" title={usuario.nombre}>
          {usuario.nombre}
        </span>
        <Button type="button" variant="outline" size="sm" onClick={() => void cerrarSesion()}>
          Cerrar sesión
        </Button>
      </div>
    ) : null

  return (
    <AppShell sidebar={<SettingsPanel />} headerExtras={headerExtras}>
      <Chat />
    </AppShell>
  )
}

function AppConSesion() {
  const { usuario } = useAuth()

  if (!usuario) {
    return <AuthScreen />
  }

  return <AppAutenticada />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <TooltipProvider delayDuration={300}>
          <AuthProvider>
            <SettingsProvider>
              <AppConSesion />
              <Toaster richColors position="top-right" />
            </SettingsProvider>
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
