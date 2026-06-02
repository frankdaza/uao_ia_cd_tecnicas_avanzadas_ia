"""Guardrails de escalacion clinica — palabras de alarma y KV (TASK-126, Ruta B)."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from src.guardrails.patrones_mensaje import PATRON_DOSIS, PATRON_FARMACO_CON_DOSIS

_PREFIJO_SESION_TELEGRAM = "telegram:"

PALABRAS_ALARMA: tuple[str, ...] = (
    "dolor intenso",
    "fiebre alta",
    "sangrado abundante",
    "dificultad respiratoria",
)

MOTIVO_ESCALADO_CLINICO = "escalado_clinico"
TIPO_AUDITORIA = "hand_escalacion"
ARCHIVO_AUDITORIA = "audit/hand_escalacion.jsonl"
SUBDIR_KV = "kv/hand_escalacion"

_DISCLAIMER_FRAGMENTOS = (
    "no reemplaza",
    "medico tratante",
    "médico tratante",
)

MENSAJE_URGENCIA = (
    "Por sus sintomas, acuda de inmediato a urgencias o contacte a su medico tratante. "
    "Este bot no puede atender emergencias. "
    "Esta orientacion no reemplaza la valoracion de su medico tratante."
)


@dataclass(frozen=True)
class ResultadoEscalacion:
    escalo: bool
    motivo: str
    mensaje: str | None = None
    frase_detectada: str | None = None


def _ahora_utc() -> datetime:
    return datetime.now(UTC)


def chat_id_desde_session_id(session_id: str) -> str | None:
    if not session_id.startswith(_PREFIJO_SESION_TELEGRAM):
        return None
    chat_id = session_id[len(_PREFIJO_SESION_TELEGRAM) :].strip()
    return chat_id or None


def debe_escalar(texto: str) -> bool:
    """True si el mensaje del paciente contiene alguna frase canonica de alarma."""
    t = texto.lower().strip()
    return any(p in t for p in PALABRAS_ALARMA)


def frase_alarma_detectada(texto: str) -> str | None:
    """Devuelve la primera frase canonica encontrada en el texto, o None."""
    t = texto.lower().strip()
    for frase in PALABRAS_ALARMA:
        if frase in t:
            return frase
    return None


def _ruta_hand_toml(raiz: Path | None = None) -> Path:
    base = raiz or Path(__file__).resolve().parents[2]
    return base / "openfang" / "hands" / "taam_lili_hand" / "HAND.toml"


def palabras_alarma_desde_hand(raiz: Path | None = None) -> list[str]:
    """Lee escalar_palabras_alarma del HAND.toml (tests de alineacion)."""
    cfg = tomllib.loads(_ruta_hand_toml(raiz).read_text(encoding="utf-8"))
    lista = cfg.get("guardrails", {}).get("escalar_palabras_alarma", [])
    if not isinstance(lista, list):
        return []
    return [str(x) for x in lista]


def redactar_mensaje_urgencia() -> str:
    return MENSAJE_URGENCIA


def validar_mensaje_urgencia(texto: str) -> list[str]:
    """Errores de validacion; lista vacia si el mensaje de urgencia es aceptable."""
    errores: list[str] = []
    bajo = texto.lower()
    if not any(fragmento in bajo for fragmento in _DISCLAIMER_FRAGMENTOS):
        errores.append("falta_disclaimer")
    if PATRON_DOSIS.search(texto):
        errores.append("contiene_dosis")
    if PATRON_FARMACO_CON_DOSIS.search(texto):
        errores.append("contiene_farmaco_con_dosis")
    return errores


def ruta_kv_escalacion(raiz_openfang: Path, chat_id: str) -> Path:
    return raiz_openfang / SUBDIR_KV / f"{chat_id}.json"


def ruta_auditoria_escalacion(raiz_openfang: Path) -> Path:
    return raiz_openfang / ARCHIVO_AUDITORIA


def leer_kv_escalacion(raiz_openfang: Path, chat_id: str) -> dict:
    ruta = ruta_kv_escalacion(raiz_openfang, chat_id)
    if not ruta.is_file():
        return {}
    return json.loads(ruta.read_text(encoding="utf-8"))


def escribir_kv_escalacion(raiz_openfang: Path, chat_id: str, kv: dict) -> Path:
    ruta = ruta_kv_escalacion(raiz_openfang, chat_id)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(kv, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def registrar_auditoria_escalacion(evento: dict, raiz_openfang: Path) -> Path:
    destino = ruta_auditoria_escalacion(raiz_openfang)
    destino.parent.mkdir(parents=True, exist_ok=True)
    linea = json.dumps(evento, ensure_ascii=False)
    with destino.open("a", encoding="utf-8") as archivo:
        archivo.write(linea + "\n")
    return destino


def marcar_escalacion(
    raiz_openfang: Path,
    session_id: str,
    texto_entrada: str,
    *,
    ahora: datetime | None = None,
) -> dict:
    """Persiste escalado=true en KV local para la sesion."""
    chat_id = chat_id_desde_session_id(session_id)
    if chat_id is None:
        raise ValueError(f"session_id invalido: {session_id}")
    instante = ahora or _ahora_utc()
    frase = frase_alarma_detectada(texto_entrada)
    kv = {
        "escalado": True,
        "session_id": session_id,
        "frase_detectada": frase,
        "ultimo_disparo_iso": instante.isoformat(),
        "texto_entrada_truncado": texto_entrada.strip()[:200],
    }
    escribir_kv_escalacion(raiz_openfang, chat_id, kv)
    return kv


def evaluar_entrada_usuario(
    session_id: str,
    texto: str,
    *,
    enviar: Callable[[str, str], None] | None = None,
    raiz_openfang: Path | None = None,
    registrar_auditoria: bool = True,
    ahora: datetime | None = None,
) -> ResultadoEscalacion:
    """Si hay alarma: marca KV, auditoria y opcionalmente envia mensaje de urgencia."""
    if not debe_escalar(texto):
        return ResultadoEscalacion(escalo=False, motivo="sin_alarma")

    raiz = raiz_openfang or Path("openfang/data")
    instante = ahora or _ahora_utc()
    chat_id = chat_id_desde_session_id(session_id)
    if chat_id is None:
        return ResultadoEscalacion(escalo=False, motivo="session_id_invalido")

    frase = frase_alarma_detectada(texto)
    marcar_escalacion(raiz, session_id, texto, ahora=instante)
    mensaje = redactar_mensaje_urgencia()

    if registrar_auditoria:
        registrar_auditoria_escalacion(
            {
                "tipo": TIPO_AUDITORIA,
                "evento": "escalacion_clinica",
                "ts_iso": instante.isoformat(),
                "session_id": session_id,
                "frase_detectada": frase,
            },
            raiz,
        )

    if enviar is not None:
        enviar(chat_id, mensaje)

    return ResultadoEscalacion(
        escalo=True,
        motivo=MOTIVO_ESCALADO_CLINICO,
        mensaje=mensaje,
        frase_detectada=frase,
    )
