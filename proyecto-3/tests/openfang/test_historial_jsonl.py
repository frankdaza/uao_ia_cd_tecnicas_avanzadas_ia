"""Pruebas de lectura JSONL bajo OPENFANG_HOME."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.openfang.historial_jsonl import (
    extraer_session_id,
    filtrar_por_session_id,
    iterar_registros_jsonl,
)

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "openfang_sesion_ejemplo.jsonl"
_SESSION = "telegram:900001"


def test_extraer_session_id() -> None:
    assert extraer_session_id({"session_id": _SESSION}) == _SESSION
    assert extraer_session_id({"sessionId": " telegram:1 "}) == "telegram:1"


def test_filtrar_por_session_id_desde_fixture(tmp_path: Path) -> None:
    destino = tmp_path / "sessions" / "900001.jsonl"
    destino.parent.mkdir(parents=True)
    shutil.copy(_FIXTURE, destino)
    audit = tmp_path / "audit" / "hand_recordatorio.jsonl"
    audit.parent.mkdir(parents=True)
    audit.write_text(
        json.dumps({"tipo": "hand_recordatorio", "session_id": _SESSION}) + "\n",
        encoding="utf-8",
    )

    registros = filtrar_por_session_id(tmp_path, _SESSION)
    assert len(registros) == 2
    assert all(r.get("session_id") == _SESSION for r in registros)

    con_audit = filtrar_por_session_id(tmp_path, _SESSION, incluir_audit=True)
    assert len(con_audit) == 3


def test_iterar_omite_audit_por_defecto(tmp_path: Path) -> None:
    ruta_audit = tmp_path / "audit" / "hand_evidencia.jsonl"
    ruta_audit.parent.mkdir(parents=True)
    ruta_audit.write_text('{"evento": "x"}\n', encoding="utf-8")
    rutas = [r for r, _ in iterar_registros_jsonl(tmp_path)]
    assert rutas == []

    rutas_audit = [r for r, _ in iterar_registros_jsonl(tmp_path, incluir_audit=True)]
    assert len(rutas_audit) == 1


def test_consultar_script_imprime_ndjson(tmp_path: Path) -> None:
    destino = tmp_path / "sessions" / "900001.jsonl"
    destino.parent.mkdir(parents=True)
    shutil.copy(_FIXTURE, destino)

    import os
    import subprocess
    import sys

    env = {**os.environ, "OPENFANG_HOME": str(tmp_path)}
    resultado = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "scripts" / "consultar_historial_sesion.py"),
            "--session-id",
            _SESSION,
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0
    lineas = [ln for ln in resultado.stdout.strip().splitlines() if ln]
    assert len(lineas) == 2
    assert json.loads(lineas[0])["role"] == "user"
