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

/** Configuración editable por el usuario en el sidebar. */
export interface Settings {
  usarOllama: boolean
  usarOpenai: boolean
  modeloOllama: string
  modeloOpenai: string
  numCtx: number
  maxTokensOpenai: number | null
  promptSistema: string | null
}

const STORAGE_KEY = 'fvl-settings-v1'

export const SETTINGS_DEFAULTS: Settings = {
  usarOllama: true,
  usarOpenai: false,
  modeloOllama: 'llama3.1:8b',
  modeloOpenai: 'gpt-4o-mini',
  numCtx: 8192,
  maxTokensOpenai: null,
  promptSistema: null,
}

function fusionarPersistido(parsed: Partial<unknown>): Settings {
  if (parsed == null || typeof parsed !== 'object') return { ...SETTINGS_DEFAULTS }
  const o = parsed as Record<string, unknown>
  const r = {
    usarOllama: typeof o.usarOllama === 'boolean' ? o.usarOllama : SETTINGS_DEFAULTS.usarOllama,
    usarOpenai:
      typeof o.usarOpenai === 'boolean' ? o.usarOpenai : SETTINGS_DEFAULTS.usarOpenai,
    modeloOllama:
      typeof o.modeloOllama === 'string' ? o.modeloOllama : SETTINGS_DEFAULTS.modeloOllama,
    modeloOpenai:
      typeof o.modeloOpenai === 'string'
        ? o.modeloOpenai
        : SETTINGS_DEFAULTS.modeloOpenai,
    numCtx:
      typeof o.numCtx === 'number' && Number.isFinite(o.numCtx)
        ? o.numCtx
        : SETTINGS_DEFAULTS.numCtx,
    maxTokensOpenai:
      typeof o.maxTokensOpenai === 'number' && Number.isFinite(o.maxTokensOpenai)
        ? o.maxTokensOpenai
        : o.maxTokensOpenai === null
          ? null
          : SETTINGS_DEFAULTS.maxTokensOpenai,
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
      usar_ollama: settings.usarOllama,
      usar_openai: settings.usarOpenai,
      modelo_ollama: settings.modeloOllama,
      modelo_openai: settings.modeloOpenai,
      num_ctx: settings.numCtx,
      max_tokens_openai: settings.maxTokensOpenai ?? undefined,
      prompt_sistema: settings.promptSistema ?? undefined,
    }),
    [
      settings.modeloOllama,
      settings.modeloOpenai,
      settings.numCtx,
      settings.promptSistema,
      settings.maxTokensOpenai,
      settings.usarOllama,
      settings.usarOpenai,
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
