import { useEffect } from 'react'
import { ThemeProvider } from 'next-themes'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AppShell } from '@/components/AppShell'
import { Button } from '@/components/ui/button'
import { AuthProvider, useAuth } from '@/features/auth/AuthContext'
import { StaffLoginScreen } from '@/features/auth/StaffLoginScreen'
import { SettingsPanel } from '@/features/settings/SettingsPanel'
import { PlaceholderCasos } from '@/features/shell/PlaceholderCasos'
import { PlaceholderHome } from '@/features/shell/PlaceholderHome'
import { useAppPath } from '@/lib/useAppPath'

const LOGIN_PATH = '/login'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

function AppRoutes({ path }: { path: string }) {
  if (path === '/casos' || path.startsWith('/casos/')) {
    return <PlaceholderCasos />
  }

  return <PlaceholderHome />
}

function AppAuthenticated() {
  const { path, setPath } = useAppPath()
  const { user, signOut } = useAuth()

  const headerExtras = user ? (
    <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] max-w-[min(220px,45vw)]">
      <span className="truncate" title={`${user.nombre} (${user.rol})`}>
        {user.nombre}
      </span>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => {
          signOut()
          setPath(LOGIN_PATH)
        }}
      >
        Cerrar sesión
      </Button>
    </div>
  ) : null

  return (
    <AppShell
      sidebar={<SettingsPanel path={path} onNavigate={setPath} />}
      headerExtras={headerExtras}
    >
      <AppRoutes path={path} />
    </AppShell>
  )
}

function AppGate() {
  const { user } = useAuth()
  const { path, setPath } = useAppPath()

  useEffect(() => {
    if (user) {
      if (path === LOGIN_PATH) {
        setPath('/')
      }
      return
    }
    if (path !== LOGIN_PATH) {
      setPath(LOGIN_PATH)
    }
  }, [user, path, setPath])

  if (!user) {
    if (path !== LOGIN_PATH) {
      return null
    }
    return <StaffLoginScreen onSuccess={() => setPath('/')} />
  }

  return <AppAuthenticated />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem storageKey="taam-theme">
        <AuthProvider>
          <AppGate />
          <Toaster richColors position="top-right" />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
