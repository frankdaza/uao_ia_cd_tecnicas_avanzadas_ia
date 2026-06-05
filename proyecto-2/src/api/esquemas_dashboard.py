"""Esquemas Pydantic para dashboards de inicio del panel TAAM."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.api.esquemas_seguimiento import AlertaTriageVista


class ConteoPorSeveridad(BaseModel):
    info: int = 0
    seguimiento: int = 0
    urgente: int = 0
    total: int = 0


class KpiAlertas(BaseModel):
    pendientes: ConteoPorSeveridad
    revisadas_ultimas_24h: int


class KpiCasos(BaseModel):
    activos: int = 0
    cerrados: int = 0
    total: int = 0
    con_telegram_vinculado: int = 0


class KpiRecordatorios(BaseModel):
    pendientes_vencidos: int = 0
    enviados_ultimas_24h: int = 0
    con_error: int = 0


class PuntoSerieAlertas(BaseModel):
    fecha: date
    cantidad: int = Field(ge=0)


class ResumenDashboardStaff(BaseModel):
    """KPIs operativos para staff (asistente, clinico, admin)."""

    generado_en: datetime
    alertas: KpiAlertas
    casos: KpiCasos
    recordatorios: KpiRecordatorios
    serie_alertas_7d: list[PuntoSerieAlertas]
    alertas_recientes: list[AlertaTriageVista] = Field(
        description="Ultimas alertas pendientes para acceso rapido.",
    )


class KpiMedicosAdmin(BaseModel):
    total: int = 0
    activos: int = 0


class KpiProcedimientosAdmin(BaseModel):
    pendiente: int = 0
    ok: int = 0
    error: int = 0
    total: int = 0


class ConfigOperativaDashboard(BaseModel):
    recordatorios_job_habilitado: bool
    recordatorios_job_interval_seg: int
    agente_hitl_habilitado: bool
    config_updated_at: datetime | None = None


class TelegramWebhookDashboard(BaseModel):
    configurado: bool
    pending_update_count: int | None = None
    last_error_message: str | None = None


class ResumenDashboardAdmin(BaseModel):
    """Metricas de sistema para administradores."""

    generado_en: datetime
    medicos: KpiMedicosAdmin
    procedimientos: KpiProcedimientosAdmin
    config_operativa: ConfigOperativaDashboard
    telegram_webhook: TelegramWebhookDashboard
