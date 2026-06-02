"""Pruebas UC6 — recordatorio postoperatorio Hand taam_lili_hand (TASK-124)."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.hand.recordatorio_postoperatorio import (
    MOTIVO_SIN_SESIONES,
    MENSAJE_GENERICO_SIN_CONTEXTO,
    TIPO_AUDITORIA,
    SesionActiva,
    ejecutar_recordatorio_postop,
    listar_sesiones_activas,
    redactar_mensaje_recordatorio,
    registrar_auditoria_hand_recordatorio,
    ruta_auditoria_hand,
    validar_mensaje_recordatorio,
)
from src.prompts.validar_hand import ruta_hand_dir

_RAIZ = Path(__file__).resolve().parents[2]
_FIXTURE_JSONL = Path(__file__).resolve().parents[1] / "fixtures" / "openfang_sesion_ejemplo.jsonl"
_AHORA = datetime(2026, 5, 23, 15, 0, 0, tzinfo=UTC)


def test_recordatorio_sin_sesiones_no_envia(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.hand.recordatorio_postoperatorio.listar_sesiones_activas",
        lambda *_a, **_k: [],
    )
    resultado = ejecutar_recordatorio_postop(
        enviar=lambda *_: None,
        registrar_auditoria=False,
        ahora=_AHORA,
    )
    assert resultado.enviados == 0
    assert resultado.motivo == MOTIVO_SIN_SESIONES


def test_recordatorio_una_sesion_llama_enviar() -> None:
    envios: list[tuple[str, str]] = []
    sesion = SesionActiva(
        session_id="telegram:12345",
        chat_id="12345",
        tiene_contexto_reciente=True,
    )

    def _listar(_raiz: Path) -> list[SesionActiva]:
        return [sesion]

    resultado = ejecutar_recordatorio_postop(
        enviar=lambda chat_id, texto: envios.append((chat_id, texto)),
        listar=_listar,
        fragmentos_por_sesion=lambda _s: ["continuar con reposo y curacion de la herida"],
        registrar_auditoria=False,
        ahora=_AHORA,
    )
    assert resultado.enviados == 1
    assert len(envios) == 1
    assert envios[0][0] == "12345"
    assert "no reemplaza" in envios[0][1].lower()


def test_mensaje_con_contexto_incluye_disclaimer() -> None:
    sesion = SesionActiva(
        session_id="telegram:1",
        chat_id="1",
        tiene_contexto_reciente=True,
    )
    texto = redactar_mensaje_recordatorio(
        sesion,
        ["mantener la zona operada seca segun indicaciones"],
    )
    assert validar_mensaje_recordatorio(texto) == []
    assert "medico tratante" in texto.lower() or "no reemplaza" in texto.lower()


def test_mensaje_sin_contexto_es_generico_sin_farmacos() -> None:
    sesion = SesionActiva(
        session_id="telegram:2",
        chat_id="2",
        tiene_contexto_reciente=False,
    )
    texto = redactar_mensaje_recordatorio(sesion, ["ibuprofeno 400 mg cada 8 horas"])
    assert texto == MENSAJE_GENERICO_SIN_CONTEXTO
    assert "ibuprofeno" not in texto.lower()
    assert validar_mensaje_recordatorio(texto) == []


def test_validar_mensaje_rechaza_dosis_mg_ml() -> None:
    texto = (
        "Tome 500 mg de acetaminofen. Esta orientacion no reemplaza "
        "la valoracion de su medico tratante."
    )
    errores = validar_mensaje_recordatorio(texto)
    assert "contiene_dosis" in errores


def test_auditoria_escribe_tipo_hand_recordatorio(tmp_path: Path) -> None:
    registrar_auditoria_hand_recordatorio(
        {
            "tipo": TIPO_AUDITORIA,
            "ts_iso": _AHORA.isoformat(),
            "enviados": 0,
            "motivo": MOTIVO_SIN_SESIONES,
        },
        tmp_path,
    )
    ruta = ruta_auditoria_hand(tmp_path)
    assert ruta.is_file()
    linea = ruta.read_text(encoding="utf-8").strip().splitlines()[-1]
    evento = json.loads(linea)
    assert evento["tipo"] == TIPO_AUDITORIA


def test_listar_sesiones_desde_jsonl_fixture(tmp_path: Path) -> None:
    destino = tmp_path / "sessions" / "chat.jsonl"
    destino.parent.mkdir(parents=True)
    shutil.copy(_FIXTURE_JSONL, destino)

    sesiones = listar_sesiones_activas(tmp_path, ahora=_AHORA)
    ids = {s.session_id for s in sesiones}
    assert "telegram:900001" in ids
    assert "telegram:900002" not in ids

    activa = next(s for s in sesiones if s.session_id == "telegram:900001")
    assert activa.tiene_contexto_reciente is True
    assert activa.chat_id == "900001"


def test_playbook_tiene_rama_sin_contexto() -> None:
    texto = (ruta_hand_dir(_RAIZ) / "prompts" / "recordatorio_postop.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "sin sesiones activas" in texto
    assert "sin contexto reciente" in texto


def test_ejecutar_registra_auditoria_sin_sesiones(tmp_path: Path) -> None:
    def _listar_vacio(_r: Path) -> list[SesionActiva]:
        return []

    ejecutar_recordatorio_postop(
        enviar=lambda *_: None,
        listar=_listar_vacio,
        raiz_openfang=tmp_path,
        registrar_auditoria=True,
        ahora=_AHORA,
    )
    evento = json.loads(
        ruta_auditoria_hand(tmp_path).read_text(encoding="utf-8").strip()
    )
    assert evento["tipo"] == TIPO_AUDITORIA
    assert evento["motivo"] == MOTIVO_SIN_SESIONES
