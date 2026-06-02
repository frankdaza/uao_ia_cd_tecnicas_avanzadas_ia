"""Pruebas guardrails escalacion clinica (TASK-126)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.guardrails.escalacion_clinica import (
    MOTIVO_ESCALADO_CLINICO,
    PALABRAS_ALARMA,
    TIPO_AUDITORIA,
    debe_escalar,
    evaluar_entrada_usuario,
    leer_kv_escalacion,
    marcar_escalacion,
    palabras_alarma_desde_hand,
    redactar_mensaje_urgencia,
    registrar_auditoria_escalacion,
    ruta_auditoria_escalacion,
    validar_mensaje_urgencia,
)

_RAIZ = Path(__file__).resolve().parents[2]
_AHORA = datetime(2026, 5, 23, 16, 0, 0, tzinfo=UTC)
_SESSION = "telegram:800001"
_CHAT = "800001"


@pytest.mark.parametrize("texto", PALABRAS_ALARMA)
def test_debe_escalar_frase_canonica(texto: str) -> None:
    assert debe_escalar(texto) is True
    assert debe_escalar(f"Tengo {texto} desde anoche") is True
    assert debe_escalar(texto.upper()) is True


@pytest.mark.parametrize(
    "texto",
    (
        "me duele un poco",
        "fiebre leve",
        "dolor normal",
        "",
        "Tengo fiebre de 38,5 °C, ¿que hago?",
    ),
)
def test_debe_escalar_negativos(texto: str) -> None:
    assert debe_escalar(texto) is False


def test_validar_mensaje_urgencia_sin_errores() -> None:
    texto = redactar_mensaje_urgencia()
    assert validar_mensaje_urgencia(texto) == []


def test_palabras_alarma_coinciden_hand_toml() -> None:
    desde_toml = palabras_alarma_desde_hand(_RAIZ)
    assert list(PALABRAS_ALARMA) == desde_toml


def test_marcar_escalacion_kv_y_auditoria(tmp_path: Path) -> None:
    marcar_escalacion(
        tmp_path,
        _SESSION,
        "tengo sangrado abundante",
        ahora=_AHORA,
    )
    kv = leer_kv_escalacion(tmp_path, _CHAT)
    assert kv.get("escalado") is True
    assert kv.get("frase_detectada") == "sangrado abundante"
    assert kv.get("session_id") == _SESSION

    registrar_auditoria_escalacion(
        {
            "tipo": TIPO_AUDITORIA,
            "evento": "escalacion_clinica",
            "ts_iso": _AHORA.isoformat(),
            "session_id": _SESSION,
        },
        tmp_path,
    )
    audit = ruta_auditoria_escalacion(tmp_path)
    assert audit.is_file()
    linea = audit.read_text(encoding="utf-8").strip().splitlines()[-1]
    evento = json.loads(linea)
    assert evento["tipo"] == TIPO_AUDITORIA


def test_evaluar_entrada_usuario_envia_mensaje(tmp_path: Path) -> None:
    envios: list[tuple[str, str]] = []

    resultado = evaluar_entrada_usuario(
        _SESSION,
        "siento dolor intenso en el pecho",
        enviar=lambda chat_id, texto: envios.append((chat_id, texto)),
        raiz_openfang=tmp_path,
        ahora=_AHORA,
    )
    assert resultado.escalo is True
    assert resultado.motivo == MOTIVO_ESCALADO_CLINICO
    assert len(envios) == 1
    assert envios[0][0] == _CHAT
    assert "urgencias" in envios[0][1].lower()
