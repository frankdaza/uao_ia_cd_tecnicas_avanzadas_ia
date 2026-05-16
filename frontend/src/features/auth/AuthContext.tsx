/* eslint-disable react-refresh/only-export-components -- modulo compartido Provider + hook (patron M2). */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { z } from 'zod'
import { postCerrarSesion, postIniciarSesion, setAuthInvalidHandler } from '@/lib/api'
import type { SesionPeticion } from '@/lib/schemas'
import { AUTH_STORAGE_KEY } from './authStorage'

const AuthPersistV1Schema = z.object({
  v: z.literal(1),
  usuarioId: z.string().uuid(),
  sessionId: z.string().min(1),
  nombre: z.string().min(1),
})

export type AuthUsuario = {
  usuarioId: string
  sessionId: string
  nombre: string
}

type AuthContextValue = {
  usuario: AuthUsuario | null
  /** Alias explícito para consumo del chat (task-59). */
  sessionId: string | null
  nombreMostrado: string | null
  iniciarSesion: (peticion: SesionPeticion) => Promise<void>
  cerrarSesion: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function leerPersistencia(): AuthUsuario | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const parsed = AuthPersistV1Schema.safeParse(JSON.parse(raw))
    if (!parsed.success) return null
    const { usuarioId, sessionId, nombre } = parsed.data
    return { usuarioId, sessionId, nombre }
  } catch {
    return null
  }
}

function escribirPersistencia(usuario: AuthUsuario) {
  const payload = { v: 1 as const, ...usuario }
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(payload))
}

function borrarPersistencia() {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<AuthUsuario | null>(() => leerPersistencia())

  useEffect(() => {
    setAuthInvalidHandler(() => {
      borrarPersistencia()
      setUsuario(null)
    })
    return () => {
      setAuthInvalidHandler(null)
    }
  }, [])

  const iniciarSesion = useCallback(async (peticion: SesionPeticion) => {
    const res = await postIniciarSesion(peticion)
    const siguiente: AuthUsuario = {
      usuarioId: res.usuario_id,
      sessionId: res.session_id,
      nombre: res.nombre,
    }
    escribirPersistencia(siguiente)
    setUsuario(siguiente)
  }, [])

  const cerrarSesion = useCallback(async () => {
    let sessionId: string | undefined
    try {
      const raw = localStorage.getItem(AUTH_STORAGE_KEY)
      if (raw) {
        const parsed = AuthPersistV1Schema.safeParse(JSON.parse(raw))
        if (parsed.success) sessionId = parsed.data.sessionId
      }
      await postCerrarSesion(sessionId)
    } catch {
      // La UI se limpia igual; la cookie puede haber expirado.
    } finally {
      borrarPersistencia()
      setUsuario(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      usuario,
      sessionId: usuario?.sessionId ?? null,
      nombreMostrado: usuario?.nombre ?? null,
      iniciarSesion,
      cerrarSesion,
    }),
    [usuario, iniciarSesion, cerrarSesion],
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
