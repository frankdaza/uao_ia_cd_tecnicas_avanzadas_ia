"""Pruebas de vectorizacion OpenAI hacia vectores.npy y metadatos.parquet (TASK-129)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from src.openfang.extraccion_tsne import (
    COLUMNAS_PARQUET,
    asignar_turnos,
    dataframe_desde_jsonl,
    escribir_parquet,
)
from src.openfang.vectorizacion_tsne import (
    COLUMNAS_METADATOS,
    SinDatosVectorizacion,
    embedir_lote,
    guardar_artefactos,
    preparar_unidades_embedding,
    vectorizar_dataframe,
)

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "openfang_sesion_ejemplo.jsonl"
_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "analisis_tsne" / "src" / "vectorizar.py"
_DIM_MOCK = 8


def _df_fixture(tmp_path: Path) -> pd.DataFrame:
    destino = tmp_path / "sessions" / "900001.jsonl"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(_FIXTURE.read_bytes())
    return asignar_turnos(dataframe_desde_jsonl(tmp_path))


def _cliente_mock_embeddings(dim: int = _DIM_MOCK) -> MagicMock:
    cliente = MagicMock()
    contador = {"llamadas": 0}

    def _create(*, model: str, input: list[str]) -> SimpleNamespace:
        contador["llamadas"] += 1
        datos = [
            SimpleNamespace(index=i, embedding=[float(i)] * dim)
            for i in range(len(input))
        ]
        return SimpleNamespace(data=datos)

    cliente.embeddings.create.side_effect = _create
    cliente._contador = contador
    return cliente


def _cliente_mock_rate_limit(dim: int = _DIM_MOCK) -> MagicMock:
    cliente = MagicMock()
    intentos = {"n": 0}

    def _create(*, model: str, input: list[str]) -> SimpleNamespace:
        intentos["n"] += 1
        if intentos["n"] <= 2:
            raise RuntimeError("rate limit")
        datos = [
            SimpleNamespace(index=i, embedding=[0.1] * dim)
            for i in range(len(input))
        ]
        return SimpleNamespace(data=datos)

    cliente.embeddings.create.side_effect = _create
    return cliente


def test_preparar_modo_sesion_dos_unidades(tmp_path: Path) -> None:
    df = _df_fixture(tmp_path)
    unidades = preparar_unidades_embedding(df, por_turno=False)
    assert len(unidades) == 2
    assert set(unidades["modo"]) == {"sesion"}
    assert unidades["turno"].isna().all()
    fila_a = unidades[unidades["session_id"] == "telegram:900001"].iloc[0]
    assert "user: Hola Bot Lili" in fila_a["texto"]
    assert "assistant:" in fila_a["texto"]


def test_preparar_modo_turno_tres_filas(tmp_path: Path) -> None:
    df = _df_fixture(tmp_path)
    unidades = preparar_unidades_embedding(df, por_turno=True)
    assert len(unidades) == 3
    assert (unidades["modo"] == "turno").all()


def test_preparar_dataframe_vacio_lanza() -> None:
    vacio = pd.DataFrame(columns=list(COLUMNAS_PARQUET))
    with pytest.raises(SinDatosVectorizacion):
        preparar_unidades_embedding(vacio, por_turno=False)


def test_embedir_lote_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(
        "src.openfang.vectorizacion_tsne.time.sleep",
        lambda s: sleeps.append(s),
    )
    cliente = _cliente_mock_rate_limit()
    resultado = embedir_lote(cliente, ["a", "b"], "text-embedding-3-small")
    assert resultado.shape == (2, _DIM_MOCK)
    assert sleeps == [1.0, 2.0]
    assert cliente.embeddings.create.call_count == 3


def test_vectorizar_dataframe_alineacion(tmp_path: Path) -> None:
    df = _df_fixture(tmp_path)
    cliente = _cliente_mock_embeddings()
    vectores, metadatos = vectorizar_dataframe(
        df,
        cliente,
        "text-embedding-3-small",
        por_turno=False,
    )
    assert vectores.dtype == np.float32
    assert vectores.shape == (2, _DIM_MOCK)
    assert list(metadatos.columns) == list(COLUMNAS_METADATOS)
    assert len(metadatos) == 2
    assert list(metadatos["indice"]) == [0, 1]


def test_vectorizar_por_turno_tres_vectores(tmp_path: Path) -> None:
    df = _df_fixture(tmp_path)
    cliente = _cliente_mock_embeddings()
    vectores, metadatos = vectorizar_dataframe(
        df,
        cliente,
        "text-embedding-3-small",
        por_turno=True,
    )
    assert vectores.shape[0] == 3
    assert (metadatos["modo"] == "turno").all()


def test_guardar_artefactos_roundtrip(tmp_path: Path) -> None:
    df = _df_fixture(tmp_path)
    cliente = _cliente_mock_embeddings()
    vectores, metadatos = vectorizar_dataframe(
        df, cliente, "text-embedding-3-small", por_turno=False
    )
    ruta_npy = tmp_path / "vectores.npy"
    ruta_parquet = tmp_path / "metadatos.parquet"
    guardar_artefactos(
        vectores,
        metadatos,
        ruta_vectores=ruta_npy,
        ruta_metadatos=ruta_parquet,
    )
    cargado = np.load(ruta_npy)
    meta = pd.read_parquet(ruta_parquet)
    assert cargado.shape == vectores.shape
    assert len(meta) == len(vectores)


def test_main_sin_datos_no_llama_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    entrada = tmp_path / "vacio.parquet"
    escribir_parquet(pd.DataFrame(columns=list(COLUMNAS_PARQUET)), entrada)
    factory = MagicMock()

    import vectorizar as modulo_vectorizar

    monkeypatch.chdir(_ROOT)
    codigo = modulo_vectorizar.main(
        ["--entrada", str(entrada), "--salida-vectores", str(tmp_path / "v.npy")],
        cliente_factory=factory,
    )
    assert codigo == 1
    factory.assert_not_called()


def test_main_exit_0_con_mock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    df = _df_fixture(tmp_path)
    entrada = tmp_path / "sesiones.parquet"
    escribir_parquet(df, entrada)
    salida_npy = tmp_path / "vectores.npy"
    salida_meta = tmp_path / "metadatos.parquet"

    import vectorizar as modulo_vectorizar

    monkeypatch.chdir(_ROOT)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-falso")
    codigo = modulo_vectorizar.main(
        [
            "--entrada",
            str(entrada),
            "--salida-vectores",
            str(salida_npy),
            "--salida-metadatos",
            str(salida_meta),
        ],
        cliente_factory=lambda _k: _cliente_mock_embeddings(),
    )
    assert codigo == 0
    assert salida_npy.is_file()
    assert salida_meta.is_file()
    assert np.load(salida_npy).shape[0] == 2


def test_main_por_turno_tres_vectores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    df = _df_fixture(tmp_path)
    entrada = tmp_path / "sesiones.parquet"
    escribir_parquet(df, entrada)
    salida_npy = tmp_path / "vectores.npy"

    import vectorizar as modulo_vectorizar

    monkeypatch.chdir(_ROOT)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-falso")
    codigo = modulo_vectorizar.main(
        [
            "--entrada",
            str(entrada),
            "--salida-vectores",
            str(salida_npy),
            "--por-turno",
        ],
        cliente_factory=lambda _k: _cliente_mock_embeddings(),
    )
    assert codigo == 0
    assert np.load(salida_npy).shape[0] == 3


def test_subprocess_sin_datos_exit_1(tmp_path: Path) -> None:
    entrada = tmp_path / "vacio.parquet"
    escribir_parquet(pd.DataFrame(columns=list(COLUMNAS_PARQUET)), entrada)
    resultado = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--entrada",
            str(entrada),
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 1
    assert "sin_datos" in resultado.stderr
