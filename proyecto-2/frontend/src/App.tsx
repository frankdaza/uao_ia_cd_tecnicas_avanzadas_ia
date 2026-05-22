import { useEffect, useRef } from 'react'
import { ThemeProvider } from 'next-themes'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { toast, Toaster } from 'sonner'
import { AppShell } from '@/components/AppShell'
import { Button } from '@/components/ui/button'
import { AdminProcedimientosRoutes } from '@/features/admin-procedimientos/AdminProcedimientosRoutes'
import { esRutaAdminProcedimientos } from '@/features/admin-procedimientos/adminProcedimientosPaths'
import { AuthProvider, useAuth } from '@/features/auth/AuthContext'
import { StaffLoginScreen } from '@/features/auth/StaffLoginScreen'
import { SettingsPanel } from '@/features/settings/SettingsPanel'
import { CasosRoutes } from '@/features/casos/CasosRoutes'
import { esRutaCasos } from '@/features/casos/casosPaths'
import { PlaceholderHome } from '@/features/shell/PlaceholderHome'
import { useAppPath } from '@/lib/useAppPath'

const LOGIN_PATH = '/login'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

function AppRoutes({ path, onNavigate }: { path: string; onNavigate: (path: string) => void }) {
  if (esRutaAdminProcedimientos(path)) {
    return <AdminProcedimientosRoutes path={path} onNavigate={onNavigate} />
  }

  if (esRutaCasos(path)) {
    return <CasosRoutes path={path} onNavigate={onNavigate} />
  }

  return <PlaceholderHome />
}

function AppAuthenticated() {
  const { path, setPath } = useAppPath()
  const { user, signOut } = useAuth()
  const adminDenegadoRef = useRef(false)

  useEffect(() => {
    if (!user || user.rol === 'admin') {
      adminDenegadoRef.current = false
      return
    }
    if (esRutaAdminProcedimientos(path)) {
      if (!adminDenegadoRef.current) {
        adminDenegadoRef.current = true
        toast.error('Solo el rol administrador puede gestionar el catálogo de procedimientos.')
      }
      setPath('/')
    }
  }, [user, path, setPath])

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
      sidebar={<SettingsPanel path={path} onNavigate={setPath} userRol={user?.rol} />}
      headerExtras={headerExtras}
    >
      <AppRoutes path={path} onNavigate={setPath} />
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
