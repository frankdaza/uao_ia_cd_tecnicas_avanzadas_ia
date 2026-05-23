"""Recordatorio postoperatorio UC6 — adaptador testeable para Hand taam_lili_hand (Ruta B)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

HORAS_CONTEXTO_RECIENTE = 48
DIAS_SESION_ACTIVA = 7
PREFIJO_SESION_TELEGRAM = "telegram:"
TIPO_AUDITORIA = "hand_recordatorio"
ARCHIVO_AUDITORIA = "audit/hand_recordatorio.jsonl"

MOTIVO_SIN_SESIONES = "sin_sesiones_activas"

from src.guardrails.patrones_mensaje import PATRON_DOSIS, PATRON_FARMACO_CON_DOSIS

_PATRON_DOSIS = PATRON_DOSIS
_PATRON_FARMACO_CON_DOSIS = PATRON_FARMACO_CON_DOSIS

_DISCLAIMER_FRAGMENTOS = (
    "no reemplaza",
    "medico tratante",
    "médico tratante",
)

MENSAJE_GENERICO_SIN_CONTEXTO = (
    "Hola, soy Bot Lili de la Fundacion Valle del Lili. "
    "Te recuerdo cuidar tu recuperacion: descanso, hidratacion y seguir las indicaciones "
    "que te dio su equipo de salud. "
    "Si tienes dolor intenso, fiebre alta, sangrado abundante o dificultad respiratoria, "
    "busca atencion de urgencias de inmediato. "
    "Esta orientacion no reemplaza la valoracion de su medico tratante. "
    "¿Tienes alguna duda sobre tu recuperacion?"
)

MENSAJE_CON_CONTEXTO_SIN_FRAGMENTOS = (
    "Hola, soy Bot Lili de la Fundacion Valle del Lili. "
    "Te recuerdo hoy continuar con los cuidados de tu recuperacion segun las indicaciones "
    "de su equipo de salud. "
    "Si tienes dolor intenso, fiebre alta, sangrado abundante o dificultad respiratoria, "
    "busca atencion de urgencias de inmediato. "
    "Esta orientacion no reemplaza la valoracion de su medico tratante. "
    "¿Tienes alguna duda sobre tu recuperacion?"
)


@dataclass(frozen=True)
class SesionActiva:
    session_id: str
    chat_id: str
    tiene_contexto_reciente: bool


@dataclass(frozen=True)
class ResultadoRecordatorioPostop:
    enviados: int
    motivo: str | None = None
    detalles: list[str] = field(default_factory=list)


def _ahora_utc() -> datetime:
    return datetime.now(UTC)


def _parsear_marca_tiempo(valor: object) -> datetime | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(float(valor), tz=UTC)
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        if texto.endswith("Z"):
            texto = texto[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(texto)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _extraer_session_id(registro: dict) -> str | None:
    for clave in ("session_id", "sessionId", "session"):
        valor = registro.get(clave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return None


def _extraer_marca_tiempo(registro: dict) -> datetime | None:
    for clave in ("ts", "timestamp", "created_at", "time", "at"):
        parsed = _parsear_marca_tiempo(registro.get(clave))
        if parsed is not None:
            return parsed
    return None


def _es_turno_conversacion(registro: dict) -> bool:
    rol = registro.get("role") or registro.get("type") or ""
    if not isinstance(rol, str):
        return False
    return rol.lower() in {"user", "assistant", "human", "ai"}


def _chat_id_desde_session_id(session_id: str) -> str | None:
    if not session_id.startswith(PREFIJO_SESION_TELEGRAM):
        return None
    chat_id = session_id[len(PREFIJO_SESION_TELEGRAM) :].strip()
    return chat_id or None


def _iterar_registros_jsonl(raiz: Path) -> list[tuple[str, dict]]:
    if not raiz.is_dir():
        return []
    filas: list[tuple[str, dict]] = []
    for ruta in sorted(raiz.rglob("*.jsonl")):
        if "hand_recordatorio" in ruta.name or "hand_evidencia" in ruta.name:
            continue
        try:
            contenido = ruta.read_text(encoding="utf-8")
        except OSError:
            logger.warning("No se pudo leer JSONL: %s", ruta)
            continue
        for linea in contenido.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            try:
                registro = json.loads(linea)
            except json.JSONDecodeError:
                continue
            if isinstance(registro, dict):
                filas.append((str(ruta), registro))
    return filas


def listar_sesiones_activas(
    raiz_openfang: Path,
    *,
    ahora: datetime | None = None,
) -> list[SesionActiva]:
    """
    Lista sesiones Telegram con actividad dentro de ``DIAS_SESION_ACTIVA``.

    Marca ``tiene_contexto_reciente`` si hubo turno user/assistant en ``HORAS_CONTEXTO_RECIENTE``.
    """
    instante = ahora or _ahora_utc()
    umbral_activa = instante - timedelta(days=DIAS_SESION_ACTIVA)
    umbral_contexto = instante - timedelta(hours=HORAS_CONTEXTO_RECIENTE)

    ultima_actividad: dict[str, datetime] = {}
    ultimo_turno: dict[str, datetime] = {}

    for _origen, registro in _iterar_registros_jsonl(raiz_openfang):
        session_id = _extraer_session_id(registro)
        if session_id is None or not session_id.startswith(PREFIJO_SESION_TELEGRAM):
            continue
        marca = _extraer_marca_tiempo(registro) or instante
        prev = ultima_actividad.get(session_id)
        if prev is None or marca > prev:
            ultima_actividad[session_id] = marca
        if _es_turno_conversacion(registro):
            prev_turno = ultimo_turno.get(session_id)
            if prev_turno is None or marca > prev_turno:
                ultimo_turno[session_id] = marca

    sesiones: list[SesionActiva] = []
    for session_id, ultima in ultima_actividad.items():
        if ultima < umbral_activa:
            continue
        chat_id = _chat_id_desde_session_id(session_id)
        if chat_id is None:
            continue
        turno = ultimo_turno.get(session_id)
        tiene_contexto = turno is not None and turno >= umbral_contexto
        sesiones.append(
            SesionActiva(
                session_id=session_id,
                chat_id=chat_id,
                tiene_contexto_reciente=tiene_contexto,
            )
        )
    return sorted(sesiones, key=lambda s: s.session_id)


def redactar_mensaje_recordatorio(
    sesion: SesionActiva,
    fragmentos_protocolo: list[str],
) -> str:
    """Redacta el texto del recordatorio sin inventar dosis ni datos clinicos."""
    if not sesion.tiene_contexto_reciente:
        return MENSAJE_GENERICO_SIN_CONTEXTO

    fragmentos_limpios = [f.strip() for f in fragmentos_protocolo if f and f.strip()]
    if not fragmentos_limpios:
        return MENSAJE_CON_CONTEXTO_SIN_FRAGMENTOS

    cuidado = fragmentos_limpios[0]
    if len(cuidado) > 280:
        cuidado = cuidado[:277] + "..."

    return (
        "Hola, soy Bot Lili de la Fundacion Valle del Lili. "
        f"Te recuerdo hoy: {cuidado} "
        "Si tienes dolor intenso, fiebre alta, sangrado abundante o dificultad respiratoria, "
        "busca atencion de urgencias de inmediato. "
        "Esta orientacion no reemplaza la valoracion de su medico tratante. "
        "¿Tienes alguna duda sobre tu recuperacion?"
    )


def validar_mensaje_recordatorio(texto: str) -> list[str]:
    """Devuelve lista de errores de validacion; vacia si el mensaje es aceptable."""
    errores: list[str] = []
    bajo = texto.lower()
    if not any(fragmento in bajo for fragmento in _DISCLAIMER_FRAGMENTOS):
        errores.append("falta_disclaimer")
    if _PATRON_DOSIS.search(texto):
        errores.append("contiene_dosis")
    if _PATRON_FARMACO_CON_DOSIS.search(texto):
        errores.append("contiene_farmaco_con_dosis")
    return errores


def ruta_auditoria_hand(raiz_openfang: Path) -> Path:
    return raiz_openfang / ARCHIVO_AUDITORIA


def registrar_auditoria_hand_recordatorio(
    evento: dict,
    raiz_openfang: Path,
) -> Path:
    """Append de una linea JSON en ``audit/hand_recordatorio.jsonl``."""
    destino = ruta_auditoria_hand(raiz_openfang)
    destino.parent.mkdir(parents=True, exist_ok=True)
    linea = json.dumps(evento, ensure_ascii=False)
    with destino.open("a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")
    return destino


def ejecutar_recordatorio_postop(
    *,
    enviar: Callable[[str, str], None],
    listar: Callable[[Path], list[SesionActiva]] | None = None,
    raiz_openfang: Path | None = None,
    fragmentos_por_sesion: Callable[[SesionActiva], list[str]] | None = None,
    registrar_auditoria: bool = True,
    ahora: datetime | None = None,
    marcar_evidencia_tras_envio: bool = False,
    accion_evidencia_solicitada: str | None = None,
) -> ResultadoRecordatorioPostop:
    """
    Orquesta el envio de recordatorios a sesiones Telegram activas.

    ``enviar(chat_id, texto)`` debe realizar el envio (p. ej. Bot API o mock en tests).
    """
    instante = ahora or _ahora_utc()
    raiz = raiz_openfang or Path("openfang/data")
    listar_fn = listar or listar_sesiones_activas
    fragmentos_fn = fragmentos_por_sesion or (lambda _s: [])

    sesiones = listar_fn(raiz)
    if not sesiones:
        logger.info("recordatorio_omitido_sin_sesiones")
        resultado = ResultadoRecordatorioPostop(
            enviados=0,
            motivo=MOTIVO_SIN_SESIONES,
            detalles=[],
        )
        if registrar_auditoria:
            registrar_auditoria_hand_recordatorio(
                {
                    "tipo": TIPO_AUDITORIA,
                    "ts_iso": instante.isoformat(),
                    "enviados": 0,
                    "motivo": MOTIVO_SIN_SESIONES,
                    "session_ids": [],
                },
                raiz,
            )
        return resultado

    detalles: list[str] = []
    enviados = 0
    session_ids_enviados: list[str] = []

    for sesion in sesiones:
        fragmentos = fragmentos_fn(sesion) if sesion.tiene_contexto_reciente else []
        texto = redactar_mensaje_recordatorio(sesion, fragmentos)
        errores = validar_mensaje_recordatorio(texto)
        if errores:
            detalles.append(f"{sesion.session_id}:validacion:{','.join(errores)}")
            logger.warning(
                "recordatorio_validacion_fallo session_id=%s errores=%s",
                sesion.session_id,
                errores,
            )
            continue
        enviar(sesion.chat_id, texto)
        enviados += 1
        session_ids_enviados.append(sesion.session_id)
        detalles.append(f"{sesion.session_id}:enviado")
        if marcar_evidencia_tras_envio:
            from src.hand.requerir_evidencia import iniciar_pendiente_evidencia

            iniciar_pendiente_evidencia(
                raiz,
                sesion.session_id,
                accion_solicitada=accion_evidencia_solicitada,
                ahora=instante,
            )
            detalles.append(f"{sesion.session_id}:evidencia_pendiente")
        logger.info(
            "recordatorio_enviado session_id=%s chat_id=%s",
            sesion.session_id,
            sesion.chat_id,
        )

    resultado = ResultadoRecordatorioPostop(
        enviados=enviados,
        motivo=None if enviados > 0 else "ningun_envio_valido",
        detalles=detalles,
    )

    if registrar_auditoria:
        registrar_auditoria_hand_recordatorio(
            {
                "tipo": TIPO_AUDITORIA,
                "ts_iso": instante.isoformat(),
                "enviados": enviados,
                "motivo": resultado.motivo,
                "session_ids": session_ids_enviados,
                "detalles": detalles,
            },
            raiz,
        )

    return resultado
