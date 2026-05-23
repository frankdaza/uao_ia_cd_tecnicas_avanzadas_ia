"""Pruebas UC7 — requerir evidencia en texto Hand taam_lili_hand (TASK-125)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.hand.requerir_evidencia import (
    HORAS_ESPERA_RESPUESTA,
    MOTIVO_CIERRE_SIN_RESPUESTA,
    MOTIVO_RESPUESTA_RECIBIDA,
    MOTIVO_SIN_PENDIENTES,
    TIPO_AUDITORIA,
    debe_cerrar_sin_respuesta,
    debe_reintentar_evidencia,
    ejecutar_requerir_evidencia,
    es_indicio_multimedia,
    iniciar_pendiente_evidencia,
    leer_kv_sesion,
    persistir_turno_evidencia,
    procesar_respuesta_evidencia,
    redactar_solicitud_evidencia,
    registrar_auditoria_hand_evidencia,
    ruta_auditoria_hand_evidencia,
)
from src.hand.recordatorio_postoperatorio import (
    SesionActiva,
    ejecutar_recordatorio_postop,
)
from src.prompts.validar_hand import ruta_hand_dir

_RAIZ = Path(__file__).resolve().parents[2]
_FIXTURE_KV = Path(__file__).resolve().parents[1] / "fixtures" / "hand_evidencia_kv_ejemplo.json"
_AHORA = datetime(2026, 5, 23, 15, 0, 0, tzinfo=UTC)
_SESSION = "telegram:900001"
_CHAT = "900001"


def _cargar_kv_fixture(clave: str) -> dict:
    datos = json.loads(_FIXTURE_KV.read_text(encoding="utf-8"))
    return dict(datos[clave])


def test_redactar_solicitud_incluye_disclaimer() -> None:
    texto = redactar_solicitud_evidencia("confirmar curacion de la herida")
    assert "no reemplaza" in texto.lower()
    assert "medico tratante" in texto.lower()
    assert "texto" in texto.lower()


def test_es_indicio_multimedia_por_texto_y_metadata() -> None:
    assert es_indicio_multimedia("te envio una foto de la herida")
    assert es_indicio_multimedia("ok", metadata={"has_attachment": True})
    assert es_indicio_multimedia("todo bien", metadata={"attachment_type": "photo"})
    assert not es_indicio_multimedia("si, tome la medicacion de la manana")


def test_debe_reintentar_tras_24h() -> None:
    kv = _cargar_kv_fixture("esperando_reintento")
    antes = _AHORA - timedelta(hours=HORAS_ESPERA_RESPUESTA)
    assert debe_reintentar_evidencia(kv, _AHORA) is True
    kv_reciente = dict(kv)
    kv_reciente["ultimo_envio_iso"] = antes.isoformat()
    assert debe_reintentar_evidencia(kv_reciente, antes + timedelta(hours=1)) is False


def test_debe_reintentar_false_si_ya_reintento() -> None:
    kv = _cargar_kv_fixture("tras_reintento")
    assert debe_reintentar_evidencia(kv, _AHORA) is False


def test_debe_cerrar_sin_respuesta_tras_reintento_y_24h() -> None:
    kv = _cargar_kv_fixture("tras_reintento")
    assert debe_cerrar_sin_respuesta(kv, _AHORA) is True
    kv_temprano = dict(kv)
    kv_temprano["ultimo_reintento_iso"] = (_AHORA - timedelta(hours=1)).isoformat()
    assert debe_cerrar_sin_respuesta(kv_temprano, _AHORA) is False


def test_solicitud_positiva_envia_y_deja_pendiente(tmp_path: Path) -> None:
    iniciar_pendiente_evidencia(tmp_path, _SESSION, ahora=_AHORA)
    envios: list[tuple[str, str]] = []

    resultado = ejecutar_requerir_evidencia(
        enviar=lambda chat_id, texto: envios.append((chat_id, texto)),
        raiz_openfang=tmp_path,
        registrar_auditoria=False,
        ahora=_AHORA,
        chat_ids=[_CHAT],
    )
    assert resultado.enviados == 1
    assert len(envios) == 1
    kv = leer_kv_sesion(tmp_path, _CHAT)
    assert kv.get("ultimo_envio_iso")
    assert kv.get("pendiente_evidencia") is True


def test_respuesta_texto_persiste_y_cierra_pendiente(tmp_path: Path) -> None:
    iniciar_pendiente_evidencia(tmp_path, _SESSION, ahora=_AHORA)
    kv_prev = leer_kv_sesion(tmp_path, _CHAT)
    kv_prev["ultimo_envio_iso"] = _AHORA.isoformat()
    from src.hand.requerir_evidencia import escribir_kv_sesion

    escribir_kv_sesion(tmp_path, _CHAT, kv_prev)

    resultado = procesar_respuesta_evidencia(
        _SESSION,
        "Si, tome la medicacion indicada",
        raiz_openfang=tmp_path,
        registrar_auditoria=False,
        ahora=_AHORA,
    )
    assert resultado.procesado is True
    assert resultado.motivo == MOTIVO_RESPUESTA_RECIBIDA
    kv = leer_kv_sesion(tmp_path, _CHAT)
    assert kv.get("pendiente_evidencia") is False
    ruta_jsonl = tmp_path / "sessions" / f"{_CHAT}.jsonl"
    assert ruta_jsonl.is_file()
    ultima = json.loads(ruta_jsonl.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert ultima["meta"]["tipo"] == "evidencia_texto"


def test_indicio_multimedia_responde_solo_texto_sin_cerrar(tmp_path: Path) -> None:
    iniciar_pendiente_evidencia(tmp_path, _SESSION, ahora=_AHORA)
    respuestas: list[str] = []
    resultado = procesar_respuesta_evidencia(
        _SESSION,
        "mira esta foto",
        enviar=lambda _c, t: respuestas.append(t),
        raiz_openfang=tmp_path,
        registrar_auditoria=False,
        ahora=_AHORA,
    )
    assert resultado.es_multimedia is True
    assert resultado.motivo == "rechazo_multimedia"
    assert len(respuestas) == 1
    assert "solo" in respuestas[0].lower() and "texto" in respuestas[0].lower()
    kv = leer_kv_sesion(tmp_path, _CHAT)
    assert kv.get("pendiente_evidencia") is True


def test_reintento_tras_24h_una_vez(tmp_path: Path) -> None:
    kv = _cargar_kv_fixture("esperando_reintento")
    from src.hand.requerir_evidencia import escribir_kv_sesion

    escribir_kv_sesion(tmp_path, _CHAT, kv)
    envios: list[str] = []
    resultado = ejecutar_requerir_evidencia(
        enviar=lambda _c, t: envios.append(t),
        raiz_openfang=tmp_path,
        registrar_auditoria=False,
        ahora=_AHORA,
        chat_ids=[_CHAT],
    )
    assert resultado.enviados == 1
    assert len(envios) == 1
    kv_despues = leer_kv_sesion(tmp_path, _CHAT)
    assert kv_despues.get("reintentos_evidencia") == 1
    assert kv_despues.get("ultimo_reintento_iso")


def test_tras_reintento_sin_respuesta_cierra_kv(tmp_path: Path) -> None:
    kv = _cargar_kv_fixture("tras_reintento")
    from src.hand.requerir_evidencia import escribir_kv_sesion

    escribir_kv_sesion(tmp_path, _CHAT, kv)
    resultado = ejecutar_requerir_evidencia(
        enviar=lambda *_: None,
        raiz_openfang=tmp_path,
        registrar_auditoria=False,
        ahora=_AHORA,
        chat_ids=[_CHAT],
    )
    assert resultado.cerrados == 1
    kv_despues = leer_kv_sesion(tmp_path, _CHAT)
    assert kv_despues.get("pendiente_evidencia") is False
    assert kv_despues.get("motivo_cierre") == MOTIVO_CIERRE_SIN_RESPUESTA


def test_ejecutar_sin_pendientes_no_envia(tmp_path: Path) -> None:
    resultado = ejecutar_requerir_evidencia(
        enviar=lambda *_: pytest.fail("no debe enviar"),
        raiz_openfang=tmp_path,
        registrar_auditoria=False,
        ahora=_AHORA,
    )
    assert resultado.enviados == 0
    assert resultado.motivo == MOTIVO_SIN_PENDIENTES


def test_auditoria_tipo_hand_evidencia(tmp_path: Path) -> None:
    registrar_auditoria_hand_evidencia(
        {
            "tipo": TIPO_AUDITORIA,
            "evento": "solicitud_enviada",
            "ts_iso": _AHORA.isoformat(),
            "session_id": _SESSION,
        },
        tmp_path,
    )
    ruta = ruta_auditoria_hand_evidencia(tmp_path)
    evento = json.loads(ruta.read_text(encoding="utf-8").strip())
    assert evento["tipo"] == TIPO_AUDITORIA


def test_playbook_tiene_ramas_negativo_y_edge() -> None:
    texto = (ruta_hand_dir(_RAIZ) / "prompts" / "requerir_evidencia.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "negativo" in texto
    assert "multimedia" in texto
    assert "24" in texto
    assert "reintento" in texto
    assert "pendiente_evidencia" in texto


def test_recordatorio_marcar_evidencia_tras_envio(tmp_path: Path) -> None:
    sesion = SesionActiva(
        session_id=_SESSION,
        chat_id=_CHAT,
        tiene_contexto_reciente=True,
    )

    def _listar(_r: Path) -> list[SesionActiva]:
        return [sesion]

    ejecutar_recordatorio_postop(
        enviar=lambda *_: None,
        listar=_listar,
        raiz_openfang=tmp_path,
        registrar_auditoria=False,
        ahora=_AHORA,
        marcar_evidencia_tras_envio=True,
    )
    kv = leer_kv_sesion(tmp_path, _CHAT)
    assert kv.get("pendiente_evidencia") is True


def test_persistir_turno_evidencia_append(tmp_path: Path) -> None:
    ruta = persistir_turno_evidencia(
        tmp_path,
        _SESSION,
        "confirmacion de prueba",
        ahora=_AHORA,
    )
    assert ruta.is_file()
    registro = json.loads(ruta.read_text(encoding="utf-8").strip())
    assert registro["session_id"] == _SESSION
