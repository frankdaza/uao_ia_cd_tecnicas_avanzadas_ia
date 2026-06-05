import type { ZodType } from 'zod'
import { formatApiDetail } from './formatApiError'
import { getAccessToken } from './authStorage'
import type {
  AlertaTriage,
  Caso,
  CasoResumenSeguimiento,
  CodigoEmparejamiento,
  DesvincularTelegram,
  ConversacionCaso,
  CrearCasoBody,
  ListadoAlertas,
  ListadoCasos,
  ListadoMedicos,
  ListadoProcedimientos,
  ListadoMedicosOpcion,
  ListadoTiposProcedimientoOpcion,
  Medico,
  Procedimiento,
  ProcedimientoMetadata,
  Salud,
  SeveridadTriage,
  StaffLoginBody,
  DisparoRecordatorioRespuesta,
  AgenteHitlConfig,
  AgenteHitlConfigParche,
  RecordatoriosJobConfig,
  RecordatoriosJobConfigParche,
  StaffLoginResponse,
  TelegramWebhookEstado,
  TelegramWebhookRegistrarCuerpo,
  TelegramWebhookRegistrarRespuesta,
} from './schemas'
import {
  AlertaTriageSchema,
  CasoResumenSeguimientoSchema,
  CasoSchema,
  CodigoEmparejamientoSchema,
  DesvincularTelegramSchema,
  ConversacionCasoSchema,
  ListadoAlertasSchema,
  ListadoCasosSchema,
  ListadoMedicosSchema,
  ListadoProcedimientosSchema,
  ListadoMedicosOpcionSchema,
  ListadoTiposProcedimientoOpcionSchema,
  MedicoSchema,
  ProcedimientoSchema,
  SaludSchema,
  DisparoRecordatorioRespuestaSchema,
  AgenteHitlConfigSchema,
  RecordatoriosJobConfigSchema,
  StaffLoginResponseSchema,
  TelegramWebhookEstadoSchema,
  TelegramWebhookRegistrarRespuestaSchema,
} from './schemas'

const BASE = '/api'

type AuthInvalidCallback = () => void
let authInvalidHandler: AuthInvalidCallback | null = null

/** Limpia sesión local cuando una petición REST devuelve 401/403 (JWT expirado o inválido). */
export function setAuthInvalidHandler(handler: AuthInvalidCallback | null): void {
  authInvalidHandler = handler
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: string | undefined

  constructor(message: string, status: number, detail?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function parseJson<T>(response: Response, schema: ZodType<T>): Promise<T> {
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      authInvalidHandler?.()
    }
    let detail: string | undefined
    try {
      const body = (await response.json()) as { detail?: unknown }
      detail = formatApiDetail(body?.detail)
    } catch {
      //
    }
    throw new ApiError(
      detail ?? `Error del servidor: ${response.status}`,
      response.status,
      detail,
    )
  }
  const json: unknown = await response.json()
  return schema.parse(json)
}

/**
 * Fetch autenticado: adjunta ``Authorization: Bearer`` si hay token en sessionStorage.
 */
export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers)
  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (
    init?.body != null &&
    !(init.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }
  return fetch(`${BASE}${path}`, { ...init, headers })
}

/** Health-check del backend TAAM (proxy Vite → :8001 en dev). */
export async function getSalud(): Promise<Salud> {
  const res = await fetch(`${BASE}/salud`)
  return parseJson(res, SaludSchema)
}

/** Inicio de sesión staff; no requiere Bearer previo. */
export async function postStaffLogin(body: StaffLoginBody): Promise<StaffLoginResponse> {
  const res = await fetch(`${BASE}/auth/staff/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJson(res, StaffLoginResponseSchema)
}

/** Listado paginado del catálogo (UC-MVP-01). */
export async function listAdminProcedimientos(params?: {
  limit?: number
  offset?: number
}): Promise<ListadoProcedimientos> {
  const qs = new URLSearchParams()
  if (params?.limit != null) qs.set('limit', String(params.limit))
  if (params?.offset != null) qs.set('offset', String(params.offset))
  const query = qs.toString()
  const res = await apiFetch(`/admin/procedimientos${query ? `?${query}` : ''}`)
  return parseJson(res, ListadoProcedimientosSchema)
}

export async function getAdminProcedimiento(id: string): Promise<Procedimiento> {
  const res = await apiFetch(`/admin/procedimientos/${id}`)
  return parseJson(res, ProcedimientoSchema)
}

export async function createAdminProcedimiento(
  metadata: ProcedimientoMetadata,
  archivo: File,
): Promise<Procedimiento> {
  const form = new FormData()
  form.append('metadata', JSON.stringify(metadata))
  form.append('archivo', archivo, archivo.name)
  const res = await apiFetch('/admin/procedimientos', { method: 'POST', body: form })
  return parseJson(res, ProcedimientoSchema)
}

export async function patchAdminProcedimiento(
  id: string,
  opts: { metadata?: Partial<ProcedimientoMetadata>; archivo?: File },
): Promise<Procedimiento> {
  const form = new FormData()
  if (opts.metadata && Object.keys(opts.metadata).length > 0) {
    form.append('metadata', JSON.stringify(opts.metadata))
  }
  if (opts.archivo) {
    form.append('archivo', opts.archivo, opts.archivo.name)
  }
  const res = await apiFetch(`/admin/procedimientos/${id}`, { method: 'PATCH', body: form })
  return parseJson(res, ProcedimientoSchema)
}

export async function reindexAdminProcedimiento(id: string): Promise<Procedimiento> {
  const res = await apiFetch(`/admin/procedimientos/${id}/reindexar`, { method: 'POST' })
  return parseJson(res, ProcedimientoSchema)
}

/** Binario del protocolo almacenado (PDF o Markdown) para vista previa admin. */
export async function fetchAdminProcedimientoProtocolo(id: string): Promise<Blob> {
  const res = await apiFetch(`/admin/procedimientos/${id}/protocolo`)
  await assertOkResponse(res)
  return res.blob()
}

async function assertOkResponse(response: Response): Promise<void> {
  if (response.ok) return
  if (response.status === 401 || response.status === 403) {
    authInvalidHandler?.()
  }
  let detail: string | undefined
  try {
    const body = (await response.json()) as { detail?: unknown }
    detail = formatApiDetail(body?.detail)
  } catch {
    //
  }
  throw new ApiError(
    detail ?? `Error del servidor: ${response.status}`,
    response.status,
    detail,
  )
}

/** Listado paginado del catálogo de médicos (admin). */
export async function listarMedicos(params?: {
  limit?: number
  offset?: number
  activo?: boolean
}): Promise<ListadoMedicos> {
  const qs = new URLSearchParams()
  if (params?.limit != null) qs.set('limit', String(params.limit))
  if (params?.offset != null) qs.set('offset', String(params.offset))
  if (params?.activo != null) qs.set('activo', String(params.activo))
  const query = qs.toString()
  const res = await apiFetch(`/admin/medicos${query ? `?${query}` : ''}`)
  return parseJson(res, ListadoMedicosSchema)
}

export async function obtenerMedico(id: string): Promise<Medico> {
  const res = await apiFetch(`/admin/medicos/${id}`)
  return parseJson(res, MedicoSchema)
}

export async function crearMedico(body: {
  codigo_registro: string
  nombre_completo: string
  especialidad?: string
}): Promise<Medico> {
  const res = await apiFetch('/admin/medicos', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return parseJson(res, MedicoSchema)
}

export async function actualizarMedico(
  id: string,
  body: {
    codigo_registro?: string
    nombre_completo?: string
    especialidad?: string | null
  },
): Promise<Medico> {
  const res = await apiFetch(`/admin/medicos/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
  return parseJson(res, MedicoSchema)
}

/** Desactiva un médico (soft delete, 204 sin cuerpo). */
export async function desactivarMedico(id: string): Promise<void> {
  const res = await apiFetch(`/admin/medicos/${id}`, { method: 'DELETE' })
  await assertOkResponse(res)
}

/** Estado del job periodico de recordatorios Telegram (solo admin). */
export async function fetchRecordatoriosJobConfig(): Promise<RecordatoriosJobConfig> {
  const res = await apiFetch('/admin/recordatorios-job')
  return parseJson(res, RecordatoriosJobConfigSchema)
}

/** Actualiza el job de recordatorios en caliente (solo admin). */
export async function patchRecordatoriosJobConfig(
  body: RecordatoriosJobConfigParche,
): Promise<RecordatoriosJobConfig> {
  const res = await apiFetch('/admin/recordatorios-job', {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
  return parseJson(res, RecordatoriosJobConfigSchema)
}

/** Estado del HITL de escalamiento del agente (solo admin). */
export async function fetchAgenteHitlConfig(): Promise<AgenteHitlConfig> {
  const res = await apiFetch('/admin/agente-hitl')
  return parseJson(res, AgenteHitlConfigSchema)
}

/** Actualiza el HITL del agente en caliente (solo admin). */
export async function patchAgenteHitlConfig(
  body: AgenteHitlConfigParche,
): Promise<AgenteHitlConfig> {
  const res = await apiFetch('/admin/agente-hitl', {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
  return parseJson(res, AgenteHitlConfigSchema)
}

/** Estado del webhook registrado en Telegram (solo admin). */
export async function fetchTelegramWebhookEstado(): Promise<TelegramWebhookEstado> {
  const res = await apiFetch('/admin/telegram-webhook')
  return parseJson(res, TelegramWebhookEstadoSchema)
}

/** Registra la URL del webhook en Telegram (setWebhook, solo admin). */
export async function registrarTelegramWebhook(
  body: TelegramWebhookRegistrarCuerpo,
): Promise<TelegramWebhookRegistrarRespuesta> {
  const res = await apiFetch('/admin/telegram-webhook', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return parseJson(res, TelegramWebhookRegistrarRespuestaSchema)
}

/** Tipos indexados para select de nuevo caso (UC-MVP-02). */
export async function listStaffTiposProcedimiento(): Promise<ListadoTiposProcedimientoOpcion> {
  const res = await apiFetch('/staff/tipos-procedimiento?indexacion_estado=ok&limit=100')
  return parseJson(res, ListadoTiposProcedimientoOpcionSchema)
}

/** Médicos activos del catálogo para combobox de cirujano (GET /api/staff/medicos). */
export async function listStaffMedicos(): Promise<ListadoMedicosOpcion> {
  const res = await apiFetch('/staff/medicos')
  return parseJson(res, ListadoMedicosOpcionSchema)
}

/** Alta de caso postoperatorio. */
export async function createStaffCaso(body: CrearCasoBody): Promise<Caso> {
  const res = await apiFetch('/staff/casos', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return parseJson(res, CasoSchema)
}

/** Listado de casos staff. */
export async function listStaffCasos(params?: {
  estado?: 'activo' | 'cerrado'
  limit?: number
  offset?: number
}): Promise<ListadoCasos> {
  const qs = new URLSearchParams()
  if (params?.estado) qs.set('estado', params.estado)
  if (params?.limit != null) qs.set('limit', String(params.limit))
  if (params?.offset != null) qs.set('offset', String(params.offset))
  const query = qs.toString()
  const res = await apiFetch(`/staff/casos${query ? `?${query}` : ''}`)
  return parseJson(res, ListadoCasosSchema)
}

/** Genera o regenera código de emparejamiento Telegram. */
export async function generateCodigoEmparejamiento(casoId: string): Promise<CodigoEmparejamiento> {
  const res = await apiFetch(`/staff/casos/${casoId}/codigo-emparejamiento`, { method: 'POST' })
  return parseJson(res, CodigoEmparejamientoSchema)
}

/** Desvincula el dispositivo Telegram activo del caso (solo rol admin). */
export async function desvincularTelegramCaso(casoId: string): Promise<DesvincularTelegram> {
  const res = await apiFetch(`/staff/casos/${casoId}/desvincular-telegram`, { method: 'POST' })
  return parseJson(res, DesvincularTelegramSchema)
}

/** Bandeja de alertas de triage (UC-MVP-05). */
export async function listStaffAlertas(params?: {
  revisado?: boolean
  severidad?: SeveridadTriage
  caso_id?: string
  limit?: number
  offset?: number
}): Promise<ListadoAlertas> {
  const qs = new URLSearchParams()
  if (params?.revisado != null) qs.set('revisado', String(params.revisado))
  if (params?.severidad) qs.set('severidad', params.severidad)
  if (params?.caso_id) qs.set('caso_id', params.caso_id)
  if (params?.limit != null) qs.set('limit', String(params.limit))
  if (params?.offset != null) qs.set('offset', String(params.offset))
  const query = qs.toString()
  const res = await apiFetch(`/staff/alertas${query ? `?${query}` : ''}`)
  return parseJson(res, ListadoAlertasSchema)
}

/** Marca una alerta como revisada (idempotente). */
export async function markAlertaRevisada(alertaId: string): Promise<AlertaTriage> {
  const res = await apiFetch(`/staff/alertas/${alertaId}`, {
    method: 'PATCH',
    body: JSON.stringify({ revisado: true }),
  })
  return parseJson(res, AlertaTriageSchema)
}

/** Historial de conversación paciente-bot por caso. */
export async function getStaffConversacion(casoId: string): Promise<ConversacionCaso> {
  const res = await apiFetch(`/staff/casos/${casoId}/conversacion`)
  return parseJson(res, ConversacionCasoSchema)
}

/** Resumen operativo del caso para seguimiento. */
export async function getStaffCasoResumen(casoId: string): Promise<CasoResumenSeguimiento> {
  const res = await apiFetch(`/staff/casos/${casoId}/resumen`)
  return parseJson(res, CasoResumenSeguimientoSchema)
}

/** Envía el siguiente recordatorio pendiente sin esperar programado_at (demo UC-MVP-04). */
export async function dispararRecordatorioPrueba(
  casoId: string,
): Promise<DisparoRecordatorioRespuesta> {
  const res = await apiFetch(`/staff/casos/${casoId}/disparar-recordatorio-prueba`, {
    method: 'POST',
  })
  return parseJson(res, DisparoRecordatorioRespuestaSchema)
}
