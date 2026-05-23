"""Pruebas de extraccion OpenFang JSONL/SQLite hacia Parquet (TASK-128)."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.openfang.extraccion_tsne import (
    COLUMNAS_PARQUET,
    asignar_turnos,
    construir_dataframe_completo,
    dataframe_desde_jsonl,
    escribir_parquet,
    fusionar_fuentes,
    normalizar_turno,
)

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "openfang_sesion_ejemplo.jsonl"
_SESSION_A = "telegram:900001"
_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "analisis_tsne" / "src" / "extraer_jsonl.py"


def _copiar_fixture_sessions(tmp_path: Path) -> Path:
    destino = tmp_path / "sessions" / "900001.jsonl"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(_FIXTURE.read_bytes())
    return tmp_path


def _crear_db_memories(ruta_db: Path) -> None:
    ruta_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ruta_db)
    conn.execute(
        """
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            scope TEXT NOT NULL DEFAULT 'episodic',
            confidence REAL NOT NULL DEFAULT 1.0,
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            accessed_at TEXT NOT NULL,
            access_count INTEGER NOT NULL DEFAULT 0,
            deleted INTEGER NOT NULL DEFAULT 0,
            embedding BLOB DEFAULT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def test_normalizar_turno_claves_alternativas() -> None:
    registro = {
        "sessionId": _SESSION_A,
        "rol": "human",
        "texto": "Hola",
        "timestamp": "2026-05-23T14:00:00+00:00",
    }
    fila = normalizar_turno(registro, ruta_origen="test.jsonl")
    assert fila is not None
    assert fila["session_id"] == _SESSION_A
    assert fila["rol"] == "user"
    assert fila["texto"] == "Hola"
    assert fila["canal"] == "telegram"


def test_omite_registro_sin_session_id_o_texto() -> None:
    assert normalizar_turno({"role": "user", "content": "x"}, ruta_origen="t") is None
    assert (
        normalizar_turno(
            {"session_id": _SESSION_A, "role": "user", "content": "  "},
            ruta_origen="t",
        )
        is None
    )


def test_dataframe_desde_fixture_tres_filas(tmp_path: Path) -> None:
    raiz = _copiar_fixture_sessions(tmp_path)
    df = dataframe_desde_jsonl(raiz)
    df = asignar_turnos(df)
    assert len(df) == 3
    assert list(df.columns) == list(COLUMNAS_PARQUET)
    filas_a = df[df["session_id"] == _SESSION_A]
    assert len(filas_a) == 2
    assert list(filas_a["turno"]) == [1, 2]


def test_turnos_ordenados_por_timestamp(tmp_path: Path) -> None:
    raiz = _copiar_fixture_sessions(tmp_path)
    df = asignar_turnos(dataframe_desde_jsonl(raiz))
    filas_a = df[df["session_id"] == _SESSION_A].sort_values("turno")
    assert filas_a.iloc[0]["texto"].startswith("Hola Bot")
    assert "recuperacion" in filas_a.iloc[1]["texto"]


def test_excluye_audit_por_defecto(tmp_path: Path) -> None:
    raiz = tmp_path
    sesion = raiz / "sessions" / "900001.jsonl"
    sesion.parent.mkdir(parents=True)
    sesion.write_bytes(_FIXTURE.read_bytes())
    audit = raiz / "audit" / "hand_recordatorio.jsonl"
    audit.parent.mkdir(parents=True)
    audit.write_text(
        json.dumps(
            {
                "tipo": "hand_recordatorio",
                "session_id": _SESSION_A,
                "role": "assistant",
                "content": "mensaje hand",
                "ts": "2026-05-23T15:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    df = asignar_turnos(dataframe_desde_jsonl(raiz))
    assert len(df) == 3
    assert "mensaje hand" not in df["texto"].tolist()


def test_incluir_audit_flag(tmp_path: Path) -> None:
    raiz = tmp_path
    sesion = raiz / "sessions" / "900001.jsonl"
    sesion.parent.mkdir(parents=True)
    sesion.write_bytes(_FIXTURE.read_bytes())
    audit = raiz / "audit" / "hand_recordatorio.jsonl"
    audit.parent.mkdir(parents=True)
    audit.write_text(
        json.dumps(
            {
                "tipo": "hand_recordatorio",
                "session_id": _SESSION_A,
                "role": "assistant",
                "content": "mensaje hand audit",
                "ts": "2026-05-23T15:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    df = asignar_turnos(dataframe_desde_jsonl(raiz, incluir_audit=True))
    assert len(df) == 4
    assert "mensaje hand audit" in df["texto"].tolist()


def test_sqlite_ausente_log_fts5_ausente(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    raiz = _copiar_fixture_sessions(tmp_path)
    ruta_db = tmp_path / "data" / "openfang.db"
    df, fts5_ausente = construir_dataframe_completo(raiz, ruta_db, solo_jsonl=True)
    assert fts5_ausente is True
    assert len(df) == 3


def test_sqlite_episodic_respaldo(tmp_path: Path) -> None:
    raiz = tmp_path / "empty_sessions"
    raiz.mkdir()
    ruta_db = tmp_path / "data" / "openfang.db"
    _crear_db_memories(ruta_db)
    conn = sqlite3.connect(ruta_db)
    conn.execute(
        """
        INSERT INTO memories (
            id, agent_id, content, source, scope, metadata,
            created_at, accessed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ep-1",
            "agent-1",
            "turno solo sqlite",
            "Chat",
            "episodic",
            json.dumps({"session_id": _SESSION_A}),
            "2026-05-23T14:00:00+00:00",
            "2026-05-23T14:00:00+00:00",
        ),
    )
    conn.commit()
    conn.close()

    df, fts5_ausente = construir_dataframe_completo(raiz, ruta_db)
    assert len(df) == 1
    assert df.iloc[0]["texto"] == "turno solo sqlite"
    assert fts5_ausente is False


def test_fusion_no_duplica_jsonl_y_sqlite(tmp_path: Path) -> None:
    raiz = _copiar_fixture_sessions(tmp_path)
    ruta_db = tmp_path / "data" / "openfang.db"
    _crear_db_memories(ruta_db)
    texto_dup = "Hola Bot Lili"
    conn = sqlite3.connect(ruta_db)
    conn.execute(
        """
        INSERT INTO memories (
            id, agent_id, content, source, scope, metadata,
            created_at, accessed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ep-dup",
            "agent-1",
            texto_dup,
            "Chat",
            "episodic",
            json.dumps({"session_id": _SESSION_A}),
            "2026-05-23T14:00:00+00:00",
            "2026-05-23T14:00:00+00:00",
        ),
    )
    conn.commit()
    conn.close()

    df, _ = construir_dataframe_completo(raiz, ruta_db)
    assert len(df) == 3
    assert (df["texto"] == texto_dup).sum() == 1


def test_parquet_roundtrip_esquema(tmp_path: Path) -> None:
    raiz = _copiar_fixture_sessions(tmp_path)
    df = asignar_turnos(dataframe_desde_jsonl(raiz))
    salida = tmp_path / "sesiones.parquet"
    escribir_parquet(df, salida)
    leido = pd.read_parquet(salida)
    assert list(leido.columns) == list(COLUMNAS_PARQUET)
    assert len(leido) == 3


def test_main_sin_datos_exit_1(tmp_path: Path) -> None:
    home = tmp_path / "vacio"
    home.mkdir()
    env = {**os.environ, "OPENFANG_HOME": str(home)}
    resultado = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 1
    assert "sin_datos" in resultado.stderr


def test_main_home_inexistente_exit_2() -> None:
    env = {**os.environ, "OPENFANG_HOME": "/ruta/inexistente/task128"}
    resultado = subprocess.run(
        [sys.executable, str(_SCRIPT), "--openfang-home", "/ruta/inexistente/task128"],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 2
    assert "openfang_home_inexistente" in resultado.stderr


def test_main_exit_0_con_fixture(tmp_path: Path) -> None:
    raiz = _copiar_fixture_sessions(tmp_path)
    salida = tmp_path / "out.parquet"
    resultado = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--openfang-home",
            str(raiz),
            "--salida",
            str(salida),
            "--solo-jsonl",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0
    assert salida.is_file()
    df = pd.read_parquet(salida)
    assert len(df) == 3


def test_fusionar_fuentes_vacio() -> None:
    vacio = pd.DataFrame(columns=list(COLUMNAS_PARQUET))
    assert fusionar_fuentes(vacio, vacio).empty
