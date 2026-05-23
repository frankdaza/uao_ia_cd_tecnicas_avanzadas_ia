"""Requerir evidencia en texto UC7 — adaptador testeable para Hand taam_lili_hand (Ruta B)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

HORAS_ESPERA_RESPUESTA = 24
PREFIJO_SESION_TELEGRAM = "telegram:"
TIPO_AUDITORIA = "hand_evidencia"
ARCHIVO_AUDITORIA = "audit/hand_evidencia.jsonl"
SUBDIR_KV = "kv/hand_evidencia"

MOTIVO_SIN_PENDIENTES = "sin_sesiones_pendientes"
MOTIVO_CIERRE_SIN_RESPUESTA = "cierre_sin_respuesta"
MOTIVO_RESPUESTA_RECIBIDA = "respuesta_recibida"

_ACCION_DEFAULT = (
    "si tomaste la dosis de la manana indicada por su equipo de salud"
)

_PATRON_MULTIMEDIA_TEXTO = re.compile(
    r"\b(?:foto|fotos|imagen|imagenes|audio|video|videos|voz|nota\s+de\s+voz|"
    r"sticker|adjunto|archivo)\b|📷|🎤|🎥",
    re.IGNORECASE,
)

_DISCLAIMER_FRAGMENTOS = (
    "no reemplaza",
    "medico tratante",
    "médico tratante",
)

MENSAJE_RECHAZO_MULTIMEDIA = (
    "Hola, en esta version del Bot Lili solo puedo registrar su confirmacion por "
    "**mensaje de texto** en el chat (no fotos, audios ni videos). "
    "Por favor escriba por ejemplo si completo la indicacion que le solicitaron. "
    "Si tiene dolor intenso, fiebre alta, sangrado abundante o dificultad respiratoria, "
    "acuda a urgencias de inmediato. "
    "Esta orientacion no reemplaza la valoracion de su medico tratante."
)


@dataclass(frozen=True)
class ResultadoRequerirEvidencia:
    enviados: int
    cerrados: int
    motivo: str | None = None
    detalles: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoProcesarEvidencia:
    procesado: bool
    es_multimedia: bool
    motivo: str
    mensaje_respuesta: str | None = None


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


def chat_id_desde_session_id(session_id: str) -> str | None:
    if not session_id.startswith(PREFIJO_SESION_TELEGRAM):
        return None
    chat_id = session_id[len(PREFIJO_SESION_TELEGRAM) :].strip()
    return chat_id or None


def session_id_desde_chat_id(chat_id: str) -> str:
    return f"{PREFIJO_SESION_TELEGRAM}{chat_id}"


def ruta_kv_sesion(raiz_openfang: Path, chat_id: str) -> Path:
    return raiz_openfang / SUBDIR_KV / f"{chat_id}.json"


def ruta_auditoria_hand_evidencia(raiz_openfang: Path) -> Path:
    return raiz_openfang / ARCHIVO_AUDITORIA


def leer_kv_sesion(raiz_openfang: Path, chat_id: str) -> dict[str, Any]:
    ruta = ruta_kv_sesion(raiz_openfang, chat_id)
    if not ruta.is_file():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("KV evidencia corrupto o ilegible: %s", ruta)
        return {}
    return datos if isinstance(datos, dict) else {}


def escribir_kv_sesion(raiz_openfang: Path, chat_id: str, kv: dict[str, Any]) -> Path:
    destino = ruta_kv_sesion(raiz_openfang, chat_id)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(kv, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def listar_chat_ids_pendientes(raiz_openfang: Path) -> list[str]:
    directorio = raiz_openfang / SUBDIR_KV
    if not directorio.is_dir():
        return []
    pendientes: list[str] = []
    for ruta in sorted(directorio.glob("*.json")):
        chat_id = ruta.stem
        kv = leer_kv_sesion(raiz_openfang, chat_id)
        if kv.get("pendiente_evidencia"):
            pendientes.append(chat_id)
    return pendientes


def _horas_desde(iso: str | None, ahora: datetime) -> float | None:
    marca = _parsear_marca_tiempo(iso)
    if marca is None:
        return None
    delta = ahora - marca
    return delta.total_seconds() / 3600.0


def debe_reintentar_evidencia(kv: dict[str, Any], ahora: datetime) -> bool:
    if not kv.get("pendiente_evidencia"):
        return False
    if int(kv.get("reintentos_evidencia", 0)) >= 1:
        return False
    horas = _horas_desde(kv.get("ultimo_envio_iso"), ahora)
    if horas is None:
        return False
    return horas >= HORAS_ESPERA_RESPUESTA


def debe_cerrar_sin_respuesta(kv: dict[str, Any], ahora: datetime) -> bool:
    if not kv.get("pendiente_evidencia"):
        return False
    if int(kv.get("reintentos_evidencia", 0)) < 1:
        return False
    referencia = kv.get("ultimo_reintento_iso") or kv.get("ultimo_envio_iso")
    horas = _horas_desde(referencia, ahora)
    if horas is None:
        return False
    return horas >= HORAS_ESPERA_RESPUESTA


def es_indicio_multimedia(texto: str, metadata: dict[str, Any] | None = None) -> bool:
    if metadata:
        if metadata.get("has_attachment"):
            return True
        tipo = metadata.get("attachment_type")
        if isinstance(tipo, str) and tipo.strip():
            bajo = tipo.lower()
            if bajo not in {"text", "texto", "message"}:
                return True
    return bool(_PATRON_MULTIMEDIA_TEXTO.search(texto))


def redactar_solicitud_evidencia(accion_solicitada: str | None = None) -> str:
    accion = (accion_solicitada or _ACCION_DEFAULT).strip()
    return (
        "Hola, para su seguimiento postoperatorio necesito que me confirme por este chat: "
        f"{accion}. "
        "Responda con un mensaje de texto (en esta version no recibo fotos, audios ni videos). "
        "Si tiene dolor intenso, fiebre alta, sangrado abundante o dificultad respiratoria, "
        "cuentemelo de inmediato y acuda a urgencias si corresponde. "
        "Esta orientacion no reemplaza la valoracion de su medico tratante."
    )


def redactar_rechazo_multimedia() -> str:
    return MENSAJE_RECHAZO_MULTIMEDIA


def validar_mensaje_solicitud_evidencia(texto: str) -> list[str]:
    errores: list[str] = []
    bajo = texto.lower()
    if not any(fragmento in bajo for fragmento in _DISCLAIMER_FRAGMENTOS):
        errores.append("falta_disclaimer")
    return errores


def iniciar_pendiente_evidencia(
    raiz_openfang: Path,
    session_id: str,
    *,
    accion_solicitada: str | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Marca solicitud de evidencia pendiente (p. ej. tras recordatorio UC6)."""
    chat_id = chat_id_desde_session_id(session_id)
    if chat_id is None:
        raise ValueError(f"session_id invalido: {session_id}")
    instante = ahora or _ahora_utc()
    kv: dict[str, Any] = {
        "pendiente_evidencia": True,
        "accion_solicitada": accion_solicitada or _ACCION_DEFAULT,
        "reintentos_evidencia": 0,
        "ultimo_envio_iso": None,
        "ultimo_reintento_iso": None,
        "motivo_cierre": None,
        "iniciado_iso": instante.isoformat(),
    }
    escribir_kv_sesion(raiz_openfang, chat_id, kv)
    return kv


def registrar_auditoria_hand_evidencia(
    evento: dict[str, Any],
    raiz_openfang: Path,
) -> Path:
    destino = ruta_auditoria_hand_evidencia(raiz_openfang)
    destino.parent.mkdir(parents=True, exist_ok=True)
    linea = json.dumps(evento, ensure_ascii=False)
    with destino.open("a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")
    return destino


def _cerrar_pendiente(
    raiz_openfang: Path,
    chat_id: str,
    kv: dict[str, Any],
    motivo_cierre: str,
) -> dict[str, Any]:
    kv = dict(kv)
    kv["pendiente_evidencia"] = False
    kv["motivo_cierre"] = motivo_cierre
    escribir_kv_sesion(raiz_openfang, chat_id, kv)
    return kv


def persistir_turno_evidencia(
    raiz_openfang: Path,
    session_id: str,
    contenido_usuario: str,
    *,
    ahora: datetime | None = None,
) -> Path:
    """Append de turno user en JSONL de sesion (memoria episodica demo)."""
    instante = ahora or _ahora_utc()
    registro = {
        "session_id": session_id,
        "role": "user",
        "content": contenido_usuario,
        "ts": instante.isoformat(),
        "meta": {"tipo": "evidencia_texto"},
    }
    directorio = raiz_openfang / "sessions"
    directorio.mkdir(parents=True, exist_ok=True)
    chat_id = chat_id_desde_session_id(session_id) or "desconocido"
    destino = directorio / f"{chat_id}.jsonl"
    linea = json.dumps(registro, ensure_ascii=False)
    with destino.open("a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")
    return destino


def ejecutar_requerir_evidencia(
    *,
    enviar: Callable[[str, str], None],
    raiz_openfang: Path | None = None,
    registrar_auditoria: bool = True,
    ahora: datetime | None = None,
    chat_ids: list[str] | None = None,
) -> ResultadoRequerirEvidencia:
    """
    Orquesta solicitudes y reintentos para sesiones con ``pendiente_evidencia``.

    No reenvia solicitud inicial si ya existe ``ultimo_envio_iso`` salvo rama de reintento.
    """
    instante = ahora or _ahora_utc()
    raiz = raiz_openfang or Path("openfang/data")
    ids = chat_ids if chat_ids is not None else listar_chat_ids_pendientes(raiz)

    if not ids:
        resultado = ResultadoRequerirEvidencia(
            enviados=0,
            cerrados=0,
            motivo=MOTIVO_SIN_PENDIENTES,
        )
        if registrar_auditoria:
            registrar_auditoria_hand_evidencia(
                {
                    "tipo": TIPO_AUDITORIA,
                    "evento": "tick_sin_pendientes",
                    "ts_iso": instante.isoformat(),
                    "enviados": 0,
                    "cerrados": 0,
                    "motivo": MOTIVO_SIN_PENDIENTES,
                },
                raiz,
            )
        return resultado

    detalles: list[str] = []
    enviados = 0
    cerrados = 0

    for chat_id in ids:
        session_id = session_id_desde_chat_id(chat_id)
        kv = leer_kv_sesion(raiz, chat_id)
        if not kv.get("pendiente_evidencia"):
            continue

        if debe_cerrar_sin_respuesta(kv, instante):
            _cerrar_pendiente(raiz, chat_id, kv, MOTIVO_CIERRE_SIN_RESPUESTA)
            cerrados += 1
            detalles.append(f"{session_id}:cerrado_sin_respuesta")
            if registrar_auditoria:
                registrar_auditoria_hand_evidencia(
                    {
                        "tipo": TIPO_AUDITORIA,
                        "evento": "cierre_sin_respuesta",
                        "ts_iso": instante.isoformat(),
                        "session_id": session_id,
                    },
                    raiz,
                )
            continue

        if debe_reintentar_evidencia(kv, instante):
            texto = redactar_solicitud_evidencia(kv.get("accion_solicitada"))
            enviar(chat_id, texto)
            kv = dict(kv)
            kv["reintentos_evidencia"] = int(kv.get("reintentos_evidencia", 0)) + 1
            kv["ultimo_reintento_iso"] = instante.isoformat()
            escribir_kv_sesion(raiz, chat_id, kv)
            enviados += 1
            detalles.append(f"{session_id}:reintento_enviado")
            if registrar_auditoria:
                registrar_auditoria_hand_evidencia(
                    {
                        "tipo": TIPO_AUDITORIA,
                        "evento": "reintento_enviado",
                        "ts_iso": instante.isoformat(),
                        "session_id": session_id,
                    },
                    raiz,
                )
            continue

        if kv.get("ultimo_envio_iso"):
            detalles.append(f"{session_id}:esperando_respuesta")
            continue

        texto = redactar_solicitud_evidencia(kv.get("accion_solicitada"))
        errores = validar_mensaje_solicitud_evidencia(texto)
        if errores:
            detalles.append(f"{session_id}:validacion:{','.join(errores)}")
            continue
        enviar(chat_id, texto)
        kv = dict(kv)
        kv["ultimo_envio_iso"] = instante.isoformat()
        escribir_kv_sesion(raiz, chat_id, kv)
        enviados += 1
        detalles.append(f"{session_id}:solicitud_enviada")
        if registrar_auditoria:
            registrar_auditoria_hand_evidencia(
                {
                    "tipo": TIPO_AUDITORIA,
                    "evento": "solicitud_enviada",
                    "ts_iso": instante.isoformat(),
                    "session_id": session_id,
                },
                raiz,
            )

    motivo = None if enviados > 0 or cerrados > 0 else "ninguna_accion"
    return ResultadoRequerirEvidencia(
        enviados=enviados,
        cerrados=cerrados,
        motivo=motivo,
        detalles=detalles,
    )


def procesar_respuesta_evidencia(
    session_id: str,
    mensaje: str,
    *,
    enviar: Callable[[str, str], None] | None = None,
    raiz_openfang: Path | None = None,
    persistir: Callable[[Path, str, str], Path] | None = None,
    registrar_auditoria: bool = True,
    ahora: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> ResultadoProcesarEvidencia:
    """Procesa mensaje entrante del paciente cuando hay evidencia pendiente."""
    instante = ahora or _ahora_utc()
    raiz = raiz_openfang or Path("openfang/data")
    chat_id = chat_id_desde_session_id(session_id)
    if chat_id is None:
        return ResultadoProcesarEvidencia(
            procesado=False,
            es_multimedia=False,
            motivo="session_id_invalido",
        )

    kv = leer_kv_sesion(raiz, chat_id)
    if not kv.get("pendiente_evidencia"):
        return ResultadoProcesarEvidencia(
            procesado=False,
            es_multimedia=False,
            motivo="sin_pendiente",
        )

    if es_indicio_multimedia(mensaje, metadata):
        texto_rechazo = redactar_rechazo_multimedia()
        if enviar is not None:
            enviar(chat_id, texto_rechazo)
        if registrar_auditoria:
            registrar_auditoria_hand_evidencia(
                {
                    "tipo": TIPO_AUDITORIA,
                    "evento": "rechazo_multimedia",
                    "ts_iso": instante.isoformat(),
                    "session_id": session_id,
                },
                raiz,
            )
        return ResultadoProcesarEvidencia(
            procesado=True,
            es_multimedia=True,
            motivo="rechazo_multimedia",
            mensaje_respuesta=texto_rechazo,
        )

    persistir_fn = persistir or persistir_turno_evidencia
    persistir_fn(raiz, session_id, mensaje.strip())
    _cerrar_pendiente(raiz, chat_id, kv, MOTIVO_RESPUESTA_RECIBIDA)
    if registrar_auditoria:
        registrar_auditoria_hand_evidencia(
            {
                "tipo": TIPO_AUDITORIA,
                "evento": "respuesta_texto_registrada",
                "ts_iso": instante.isoformat(),
                "session_id": session_id,
            },
            raiz,
        )
    return ResultadoProcesarEvidencia(
        procesado=True,
        es_multimedia=False,
        motivo=MOTIVO_RESPUESTA_RECIBIDA,
    )
