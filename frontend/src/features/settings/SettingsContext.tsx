import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import type { QaPeticion } from '@/lib/schemas'

/** Configuración editable por el usuario en el sidebar (solo OpenAI). */
export interface Settings {
  modeloOpenai: string
  maxTokensOpenai: number | null
  temperatura: number
  topP: number
  promptSistema: string | null
}

const STORAGE_KEY = 'fvl-settings-v2'

export const SETTINGS_DEFAULTS: Settings = {
  modeloOpenai: 'gpt-4o-mini',
  maxTokensOpenai: null,
  temperatura: 0.2,
  topP: 1,
  promptSistema: null,
}

function fusionarPersistido(parsed: Partial<unknown>): Settings {
  if (parsed == null || typeof parsed !== 'object') return { ...SETTINGS_DEFAULTS }
  const o = parsed as Record<string, unknown>
  const r = {
    modeloOpenai:
      typeof o.modeloOpenai === 'string' ? o.modeloOpenai : SETTINGS_DEFAULTS.modeloOpenai,
    maxTokensOpenai:
      typeof o.maxTokensOpenai === 'number' && Number.isFinite(o.maxTokensOpenai)
        ? o.maxTokensOpenai
        : o.maxTokensOpenai === null
          ? null
          : SETTINGS_DEFAULTS.maxTokensOpenai,
    temperatura:
      typeof o.temperatura === 'number' && Number.isFinite(o.temperatura)
        ? o.temperatura
        : SETTINGS_DEFAULTS.temperatura,
    topP:
      typeof o.topP === 'number' && Number.isFinite(o.topP) ? o.topP : SETTINGS_DEFAULTS.topP,
    promptSistema:
      typeof o.promptSistema === 'string'
        ? o.promptSistema
        : o.promptSistema === null
          ? null
          : SETTINGS_DEFAULTS.promptSistema,
  }
  return r
}

function leerPersistido(): Settings | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return fusionarPersistido(JSON.parse(raw) as Partial<unknown>)
  } catch {
    return null
  }
}

interface SettingsContextValue {
  settings: Settings
  updateSettings: (partial: Partial<Settings>) => void
  toQaPeticion: (pregunta: string) => QaPeticion
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const initRef = useRef(false)
  const [settings, setSettings] = useState<Settings>(() => leerPersistido() ?? {
    ...SETTINGS_DEFAULTS,
  })

  useEffect(() => {
    if (!initRef.current) {
      initRef.current = true
      return
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch {
      // ignorar escritura si localStorage bloqueado
    }
  }, [settings])

  const updateSettings = useCallback((partial: Partial<Settings>) => {
    setSettings((prev) => ({ ...prev, ...partial }))
  }, [])

  const toQaPeticion = useCallback(
    (pregunta: string): QaPeticion => ({
      pregunta,
      modelo_openai: settings.modeloOpenai,
      max_tokens_openai: settings.maxTokensOpenai ?? undefined,
      temperatura: settings.temperatura,
      top_p: settings.topP,
      prompt_sistema: settings.promptSistema ?? undefined,
    }),
    [
      settings.modeloOpenai,
      settings.maxTokensOpenai,
      settings.temperatura,
      settings.topP,
      settings.promptSistema,
    ],
  )

  const value = useMemo(
    () => ({ settings, updateSettings, toQaPeticion }),
    [settings, updateSettings, toQaPeticion],
  )

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings debe usarse dentro de SettingsProvider')
  return ctx
}
