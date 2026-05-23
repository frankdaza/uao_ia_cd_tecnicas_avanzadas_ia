import { z } from 'zod'

export const AUTH_STORAGE_KEY = 'taam-staff-auth-v1'

export const StaffAuthPersistV1Schema = z.object({
  accessToken: z.string().min(1),
  email: z.string().email(),
  nombre: z.string().min(1),
  rol: z.string().min(1),
})

export type StaffAuthPersistV1 = z.infer<typeof StaffAuthPersistV1Schema>

export function readAuthPersist(): StaffAuthPersistV1 | null {
  try {
    const raw = sessionStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const parsed = StaffAuthPersistV1Schema.safeParse(JSON.parse(raw))
    return parsed.success ? parsed.data : null
  } catch {
    return null
  }
}

export function writeAuthPersist(data: StaffAuthPersistV1): void {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data))
}

export function clearAuthPersist(): void {
  sessionStorage.removeItem(AUTH_STORAGE_KEY)
}

export function getAccessToken(): string | null {
  return readAuthPersist()?.accessToken ?? null
}
