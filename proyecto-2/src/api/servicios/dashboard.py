"""Agregacion de KPIs para dashboards de inicio."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.esquemas_dashboard import (
    ConfigOperativaDashboard,
    ConteoPorSeveridad,
    KpiAlertas,
    KpiCasos,
    KpiMedicosAdmin,
    KpiProcedimientosAdmin,
    KpiRecordatorios,
    PuntoSerieAlertas,
    ResumenDashboardAdmin,
    ResumenDashboardStaff,
    TelegramWebhookDashboard,
)
from src.api.servicios.seguimiento_caso import alerta_a_vista
from src.configuracion import Configuracion, obtener_configuracion
from src.integracion.telegram.configuracion_webhook import (
    TelegramApiRespuestaError,
    TelegramWebhookConfiguracionError,
    obtener_estado_webhook,
)
from src.persistencia.modelos import UsuarioStaff
from src.persistencia.repositorios.alertas_triage import RepositorioAlertasTriage
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.config_operativa_taam import RepositorioConfigOperativaTaam
from src.persistencia.repositorios.medicos import RepositorioMedicos
from src.persistencia.repositorios.recordatorios_enviados import RepositorioRecordatoriosEnviados
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram

_DIAS_SERIE = 7
_LIMITE_ALERTAS_RECIENTES = 8


def _conteo_severidad(mapa: dict[str, int]) -> ConteoPorSeveridad:
    info = mapa.get("info", 0)
    seguimiento = mapa.get("seguimiento", 0)
    urgente = mapa.get("urgente", 0)
    return ConteoPorSeveridad(
        info=info,
        seguimiento=seguimiento,
        urgente=urgente,
        total=info + seguimiento + urgente,
    )


def _rellenar_serie_7d(
    puntos_db: list[tuple[date, int]],
    *,
    ahora: datetime,
) -> list[PuntoSerieAlertas]:
    hoy = ahora.astimezone(UTC).date()
    inicio = hoy - timedelta(days=_DIAS_SERIE - 1)
    mapa = {dia: cnt for dia, cnt in puntos_db}
    serie: list[PuntoSerieAlertas] = []
    for i in range(_DIAS_SERIE):
        dia = inicio + timedelta(days=i)
        serie.append(PuntoSerieAlertas(fecha=dia, cantidad=mapa.get(dia, 0)))
    return serie


async def construir_resumen_dashboard_staff(
    sesion: AsyncSession,
    *,
    staff: UsuarioStaff,
) -> ResumenDashboardStaff:
    ahora = datetime.now(UTC)
    hace_24h = ahora - timedelta(hours=24)

    repo_alertas = RepositorioAlertasTriage(sesion)
    pendientes_mapa = await repo_alertas.contar_por_severidad(revisado=False)
    revisadas_24h = await repo_alertas.contar_revisadas_desde(hace_24h)
    serie_raw = await repo_alertas.serie_creadas_por_dia(dias=_DIAS_SERIE)

    repo_casos = RepositorioCasosPostoperatorio(sesion)
    casos_mapa = await repo_casos.contar_por_estado()
    activos = casos_mapa.get("activo", 0)
    cerrados = casos_mapa.get("cerrado", 0)

    repo_vinculos = RepositorioVinculosTelegram(sesion)
    vinculados = await repo_vinculos.contar_activos()

    repo_recordatorios = RepositorioRecordatoriosEnviados(sesion)
    recordatorios_mapa = await repo_recordatorios.contar_por_estado()
    enviados_24h = await repo_recordatorios.contar_enviados_desde(hace_24h)
    vencidos = await repo_recordatorios.contar_pendientes_vencidos(ahora=ahora)

    alertas_recientes: list = []
    filas_pendientes = await repo_alertas.listar(
        revisado=False,
        limite=_LIMITE_ALERTAS_RECIENTES,
        offset=0,
    )
    for alerta in filas_pendientes:
        caso = await repo_casos.obtener_por_id(alerta.caso_id)
        if caso is None:
            continue
        alertas_recientes.append(alerta_a_vista(alerta, caso, rol_staff=staff.rol))

    return ResumenDashboardStaff(
        generado_en=ahora,
        alertas=KpiAlertas(
            pendientes=_conteo_severidad(pendientes_mapa),
            revisadas_ultimas_24h=revisadas_24h,
        ),
        casos=KpiCasos(
            activos=activos,
            cerrados=cerrados,
            total=activos + cerrados,
            con_telegram_vinculado=vinculados,
        ),
        recordatorios=KpiRecordatorios(
            pendientes_vencidos=vencidos,
            enviados_ultimas_24h=enviados_24h,
            con_error=recordatorios_mapa.get("error", 0),
        ),
        serie_alertas_7d=_rellenar_serie_7d(serie_raw, ahora=ahora),
        alertas_recientes=alertas_recientes,
    )


async def construir_resumen_dashboard_admin(
    sesion: AsyncSession,
    *,
    cfg: Configuracion | None = None,
) -> ResumenDashboardAdmin:
    ahora = datetime.now(UTC)
    cfg = cfg or obtener_configuracion()

    repo_medicos = RepositorioMedicos(sesion)
    total_medicos = await repo_medicos.contar()
    activos_medicos = await repo_medicos.contar(activo=True)

    repo_tipos = RepositorioTiposProcedimiento(sesion)
    indexacion_mapa = await repo_tipos.contar_por_indexacion_estado()
    pendiente = indexacion_mapa.get("pendiente", 0)
    ok = indexacion_mapa.get("ok", 0)
    error = indexacion_mapa.get("error", 0)

    repo_config = RepositorioConfigOperativaTaam(sesion)
    fila_config = await repo_config.obtener_o_crear_desde_env(cfg)

    webhook_vista = TelegramWebhookDashboard(configurado=False)
    try:
        estado_tg = await obtener_estado_webhook()
        webhook_vista = TelegramWebhookDashboard(
            configurado=estado_tg.configurado,
            pending_update_count=estado_tg.pending_update_count,
            last_error_message=estado_tg.last_error_message,
        )
    except (TelegramWebhookConfiguracionError, TelegramApiRespuestaError):
        pass

    return ResumenDashboardAdmin(
        generado_en=ahora,
        medicos=KpiMedicosAdmin(total=total_medicos, activos=activos_medicos),
        procedimientos=KpiProcedimientosAdmin(
            pendiente=pendiente,
            ok=ok,
            error=error,
            total=pendiente + ok + error,
        ),
        config_operativa=ConfigOperativaDashboard(
            recordatorios_job_habilitado=fila_config.recordatorios_job_habilitado,
            recordatorios_job_interval_seg=fila_config.recordatorios_job_interval_seg,
            agente_hitl_habilitado=fila_config.agente_hitl_escalar_habilitado,
            config_updated_at=fila_config.updated_at,
        ),
        telegram_webhook=webhook_vista,
    )
