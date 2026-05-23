import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { toast } from 'sonner'
import { postStaffLogin, setAuthInvalidHandler } from '@/lib/api'
import {
  clearAuthPersist,
  readAuthPersist,
  writeAuthPersist,
  type StaffAuthPersistV1,
} from '@/lib/authStorage'
import type { StaffLoginBody } from '@/lib/schemas'

export interface StaffUser {
  email: string
  nombre: string
  rol: string
}

interface AuthContextValue {
  user: StaffUser | null
  accessToken: string | null
  signIn: (body: StaffLoginBody) => Promise<void>
  signOut: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function persistToUser(data: StaffAuthPersistV1): StaffUser {
  return { email: data.email, nombre: data.nombre, rol: data.rol }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [persist, setPersist] = useState<StaffAuthPersistV1 | null>(() => readAuthPersist())

  useEffect(() => {
    setAuthInvalidHandler(() => {
      clearAuthPersist()
      setPersist(null)
      toast.error('La sesión expiró o no es válida. Inicie sesión de nuevo.')
    })
    return () => setAuthInvalidHandler(null)
  }, [])

  const signIn = useCallback(async (body: StaffLoginBody) => {
    const res = await postStaffLogin(body)
    const next: StaffAuthPersistV1 = {
      accessToken: res.access_token,
      email: body.email,
      nombre: res.nombre,
      rol: res.rol,
    }
    writeAuthPersist(next)
    setPersist(next)
  }, [])

  const signOut = useCallback(() => {
    clearAuthPersist()
    setPersist(null)
  }, [])

  const user = persist ? persistToUser(persist) : null

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken: persist?.accessToken ?? null,
      signIn,
      signOut,
    }),
    [user, persist, signIn, signOut],
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
