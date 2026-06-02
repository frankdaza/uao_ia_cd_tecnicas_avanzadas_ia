"""Vectorizacion OpenAI de transcripciones t-SNE (sesion o turno)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd

COLUMNAS_METADATOS = (
    "indice",
    "session_id",
    "canal",
    "turno",
    "rol",
    "texto",
    "modo",
    "timestamp",
)


class SinDatosVectorizacion(Exception):
    """No hay filas utiles para embedir (parquet vacio o sin texto)."""


class _ClienteEmbeddings(Protocol):
    class _Embeddings:
        def create(self, *, model: str, input: list[str]) -> object: ...

    embeddings: _Embeddings


def preparar_unidades_embedding(df: pd.DataFrame, *, por_turno: bool) -> pd.DataFrame:
    """
    Prepara una fila por unidad a embedir.

    Modo turno: una fila por fila del parquet (con texto no vacio).
    Modo sesion: una fila por session_id con transcripcion concatenada.
    """
    if df.empty:
        raise SinDatosVectorizacion("dataframe vacio")

    requeridas = {"session_id", "texto", "turno", "rol", "canal", "timestamp"}
    faltantes = requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"columnas faltantes en parquet: {sorted(faltantes)}")

    base = df.copy()
    base["texto"] = base["texto"].astype(str).str.strip()
    base = base[base["texto"] != ""]
    if base.empty:
        raise SinDatosVectorizacion("sin textos tras filtrar vacios")

    if por_turno:
        salida = base.sort_values(["session_id", "turno"]).reset_index(drop=True)
        salida = salida.assign(modo="turno")
        return salida[["session_id", "canal", "turno", "rol", "texto", "modo", "timestamp"]]

    filas: list[dict[str, object]] = []
    for session_id, grupo in base.groupby("session_id", sort=True):
        ordenado = grupo.sort_values("turno")
        lineas = [f"{row['rol']}: {row['texto']}" for _, row in ordenado.iterrows()]
        texto_sesion = "\n".join(lineas)
        ultimo = ordenado.iloc[-1]
        filas.append(
            {
                "session_id": session_id,
                "canal": ultimo["canal"],
                "turno": pd.NA,
                "rol": pd.NA,
                "texto": texto_sesion,
                "modo": "sesion",
                "timestamp": ultimo["timestamp"],
            }
        )

    if not filas:
        raise SinDatosVectorizacion("sin sesiones tras agrupar")

    return pd.DataFrame(filas)


def embedir_lote(cliente: _ClienteEmbeddings, textos: list[str], modelo: str) -> np.ndarray:
    """Llama embeddings.create con backoff exponencial (max 3 intentos)."""
    for intento in range(3):
        try:
            resp = cliente.embeddings.create(model=modelo, input=textos)
            datos = sorted(resp.data, key=lambda item: item.index)
            return np.array([item.embedding for item in datos], dtype=np.float32)
        except Exception:
            if intento == 2:
                raise
            time.sleep(2**intento)
    raise RuntimeError("no alcanzable")


def vectorizar_dataframe(
    df: pd.DataFrame,
    cliente: _ClienteEmbeddings,
    modelo: str,
    *,
    por_turno: bool = False,
    tam_lote: int = 32,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Genera vectores y metadatos alineados por indice."""
    unidades = preparar_unidades_embedding(df, por_turno=por_turno)
    textos = unidades["texto"].tolist()
    vectores_lista: list[np.ndarray] = []

    for inicio in range(0, len(textos), tam_lote):
        lote = textos[inicio : inicio + tam_lote]
        vectores_lista.append(embedir_lote(cliente, lote, modelo))

    if not vectores_lista:
        raise SinDatosVectorizacion("sin lotes para vectorizar")

    vectores = np.vstack(vectores_lista)
    metadatos = unidades.copy()
    metadatos.insert(0, "indice", range(len(metadatos)))
    metadatos = metadatos[list(COLUMNAS_METADATOS)]

    if len(metadatos) != vectores.shape[0]:
        raise RuntimeError("desalineacion entre metadatos y vectores")

    return vectores, metadatos


def guardar_artefactos(
    vectores: np.ndarray,
    metadatos: pd.DataFrame,
    *,
    ruta_vectores: Path,
    ruta_metadatos: Path,
) -> None:
    """Persiste vectores.npy y metadatos.parquet."""
    ruta_vectores.parent.mkdir(parents=True, exist_ok=True)
    ruta_metadatos.parent.mkdir(parents=True, exist_ok=True)
    np.save(ruta_vectores, vectores)
    metadatos.to_parquet(ruta_metadatos, index=False)


def cargar_sesiones_parquet(ruta: Path) -> pd.DataFrame:
    """Lee el parquet producido por extraer_jsonl."""
    if not ruta.is_file():
        raise FileNotFoundError(f"entrada inexistente: {ruta}")
    return pd.read_parquet(ruta)
