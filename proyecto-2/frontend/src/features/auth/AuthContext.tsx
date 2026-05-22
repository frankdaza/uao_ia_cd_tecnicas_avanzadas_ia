import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

/** Perfil staff mínimo; TASK-110 completará login JWT. */
export interface StaffUser {
  email: string
  nombre: string
  rol: string
}

interface AuthContextValue {
  user: StaffUser | null
  /** Marca sesión de desarrollo hasta existir login real. */
  setDevSession: (user: StaffUser | null) => void
  signOut: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

const DEV_SESSION_KEY = 'taam-dev-staff-session'

function readDevSession(): StaffUser | null {
  try {
    const raw = sessionStorage.getItem(DEV_SESSION_KEY)
    if (!raw) return null
    return JSON.parse(raw) as StaffUser
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<StaffUser | null>(() => readDevSession())

  const setDevSession = useCallback((next: StaffUser | null) => {
    setUser(next)
    try {
      if (next) {
        sessionStorage.setItem(DEV_SESSION_KEY, JSON.stringify(next))
      } else {
        sessionStorage.removeItem(DEV_SESSION_KEY)
      }
    } catch {
      //
    }
  }, [])

  const signOut = useCallback(() => setDevSession(null), [setDevSession])

  const value = useMemo(
    () => ({ user, setDevSession, signOut }),
    [user, setDevSession, signOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth debe usarse dentro de AuthProvider')
  }
  return ctx
}
