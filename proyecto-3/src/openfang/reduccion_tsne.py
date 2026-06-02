"""Reduccion t-SNE, clustering KMeans y export Plotly para analisis bonus M3."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score

MIN_SESIONES_TSNE = 3
PERPLEJIDAD_MIN_OBJETIVO = 5
PERPLEJIDAD_MAX_OBJETIVO = 30


class SesionesInsuficientesTsne(Exception):
    """Menos sesiones unicas que el minimo para ejecutar t-SNE."""


@dataclass(frozen=True)
class ResultadoPipelineTsne:
    """Salida del pipeline de reduccion y clustering."""

    coords_2d: np.ndarray
    coords_3d: np.ndarray
    etiquetas: np.ndarray
    n_clusters: int
    perplexity: float
    n_sesiones: int


def contar_sesiones(metadatos: pd.DataFrame) -> int:
    """Cuenta session_id unicos en metadatos de vectorizacion."""
    if metadatos.empty or "session_id" not in metadatos.columns:
        return 0
    return int(metadatos["session_id"].nunique())


def sesiones_insuficientes(n_sesiones: int, minimo: int = MIN_SESIONES_TSNE) -> bool:
    """True si no hay suficientes sesiones para t-SNE estable."""
    return n_sesiones < minimo


def perplejidad_adaptiva(
    n_muestras: int,
    *,
    minimo_objetivo: int = PERPLEJIDAD_MIN_OBJETIVO,
    maximo_objetivo: int = PERPLEJIDAD_MAX_OBJETIVO,
) -> float:
    """
    Perplejidad para TSNE: objetivo en [5, 30], acotada por sklearn (perplexity < n).

    Con n=3 el limite de sklearn es 2 (excepcion documentada frente al rango 5-30).
    """
    if n_muestras < 2:
        raise ValueError(f"se requieren al menos 2 muestras, recibido {n_muestras}")
    limite_sklearn = n_muestras - 1
    objetivo = min(maximo_objetivo, max(minimo_objetivo, limite_sklearn))
    return float(min(objetivo, limite_sklearn))


def elegir_k_clusters(
    x: np.ndarray,
    *,
    k_min: int = 3,
    k_max: int = 5,
    random_state: int = 42,
) -> int:
    """Elige k en [k_min, k_max] maximizando silhouette_score."""
    n = x.shape[0]
    if n < k_min:
        return max(1, n)
    k_max_efectivo = min(k_max, n)
    if k_max_efectivo < k_min:
        return k_max_efectivo

    mejor_k = k_min
    mejor_score = -1.0
    for k in range(k_min, k_max_efectivo + 1):
        if k >= n:
            break
        modelo = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        etiquetas = modelo.fit_predict(x)
        if len(np.unique(etiquetas)) < 2:
            continue
        score = silhouette_score(x, etiquetas)
        if score > mejor_score:
            mejor_score = score
            mejor_k = k
    return mejor_k


def reducir_tsne(
    x: np.ndarray,
    *,
    n_components: int,
    perplexity: float,
    random_state: int = 42,
) -> np.ndarray:
    """Aplica TSNE sobre la matriz de embeddings."""
    modelo = TSNE(
        n_components=n_components,
        perplexity=perplexity,
        random_state=random_state,
        init="pca",
        learning_rate="auto",
    )
    return modelo.fit_transform(x)


def etiquetar_kmeans(
    x: np.ndarray,
    n_clusters: int,
    *,
    random_state: int = 42,
) -> np.ndarray:
    """Clustering KMeans en el espacio de embeddings (no en coords t-SNE)."""
    modelo = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    return modelo.fit_predict(x)


def _construir_hover(metadatos: pd.DataFrame) -> list[str]:
    textos = metadatos.get("texto", pd.Series(dtype=str)).astype(str)
    return [t[:120] + ("..." if len(t) > 120 else "") for t in textos]


def exportar_plotly(
    coords_2d: np.ndarray,
    coords_3d: np.ndarray,
    etiquetas: np.ndarray,
    metadatos: pd.DataFrame,
    *,
    dir_salida: Path,
    nombre_png: str = "tsne_2d.png",
    nombre_html: str = "tsne_3d.html",
) -> tuple[Path, Path]:
    """Exporta scatter 2D (PNG) y 3D interactivo (HTML)."""
    dir_salida.mkdir(parents=True, exist_ok=True)
    ruta_png = dir_salida / nombre_png
    ruta_html = dir_salida / nombre_html

    etiquetas_str = etiquetas.astype(str)
    hover = _construir_hover(metadatos)
    df_plot = pd.DataFrame(
        {
            "x2": coords_2d[:, 0],
            "y2": coords_2d[:, 1],
            "x3": coords_3d[:, 0],
            "y3": coords_3d[:, 1],
            "z3": coords_3d[:, 2],
            "cluster": etiquetas_str,
            "session_id": metadatos["session_id"].astype(str).tolist(),
            "hover": hover,
        }
    )

    fig_2d = px.scatter(
        df_plot,
        x="x2",
        y="y2",
        color="cluster",
        hover_name="session_id",
        custom_data=["hover"],
        title="t-SNE 2D — clusters de intencion (embeddings OpenAI)",
    )
    fig_2d.update_traces(marker={"size": 10, "opacity": 0.85})
    fig_2d.write_image(str(ruta_png), width=900, height=600, scale=2)

    fig_3d = px.scatter_3d(
        df_plot,
        x="x3",
        y="y3",
        z="z3",
        color="cluster",
        hover_name="session_id",
        custom_data=["hover"],
        title="t-SNE 3D — clusters de intencion (embeddings OpenAI)",
    )
    fig_3d.update_traces(marker={"size": 5, "opacity": 0.85})
    fig_3d.write_html(str(ruta_html), include_plotlyjs="cdn")

    return ruta_png, ruta_html


def resumen_clusters_por_etiqueta(
    metadatos: pd.DataFrame,
    etiquetas: np.ndarray,
    *,
    max_ejemplos: int = 2,
    max_caracteres: int = 80,
) -> dict[int, list[str]]:
    """Ejemplos de texto por cluster (truncados, sin expandir PHI)."""
    resumen: dict[int, list[str]] = {}
    textos = metadatos.get("texto", pd.Series(dtype=str)).astype(str)
    for etiqueta in sorted(np.unique(etiquetas)):
        mascara = etiquetas == etiqueta
        ejemplos: list[str] = []
        for texto in textos[mascara].head(max_ejemplos):
            limpio = " ".join(str(texto).split())
            if len(limpio) > max_caracteres:
                limpio = limpio[: max_caracteres - 3] + "..."
            if limpio:
                ejemplos.append(limpio)
        resumen[int(etiqueta)] = ejemplos
    return resumen


def cargar_artefactos_vectorizacion(
    ruta_vectores: Path,
    ruta_metadatos: Path,
) -> tuple[np.ndarray, pd.DataFrame]:
    """Carga vectores.npy y metadatos.parquet alineados."""
    if not ruta_vectores.is_file():
        raise FileNotFoundError(f"vectores inexistentes: {ruta_vectores}")
    if not ruta_metadatos.is_file():
        raise FileNotFoundError(f"metadatos inexistentes: {ruta_metadatos}")
    vectores = np.load(ruta_vectores)
    metadatos = pd.read_parquet(ruta_metadatos)
    if len(metadatos) != vectores.shape[0]:
        raise ValueError("desalineacion entre metadatos y vectores")
    return vectores, metadatos


def ejecutar_pipeline_visual(
    x: np.ndarray,
    metadatos: pd.DataFrame,
    dir_salida: Path,
    *,
    random_state: int = 42,
    k_min: int = 3,
    k_max: int = 5,
) -> ResultadoPipelineTsne:
    """Pipeline completo: guard sesiones, KMeans, t-SNE 2D/3D, export Plotly."""
    n_sesiones = contar_sesiones(metadatos)
    if sesiones_insuficientes(n_sesiones):
        raise SesionesInsuficientesTsne(
            f"solo {n_sesiones} sesiones; se requieren al menos {MIN_SESIONES_TSNE}"
        )

    n_muestras = x.shape[0]
    perplexity = perplejidad_adaptiva(n_muestras)
    n_clusters = elegir_k_clusters(x, k_min=k_min, k_max=k_max, random_state=random_state)
    etiquetas = etiquetar_kmeans(x, n_clusters, random_state=random_state)

    coords_2d = reducir_tsne(
        x, n_components=2, perplexity=perplexity, random_state=random_state
    )
    coords_3d = reducir_tsne(
        x, n_components=3, perplexity=perplexity, random_state=random_state
    )
    exportar_plotly(coords_2d, coords_3d, etiquetas, metadatos, dir_salida=dir_salida)

    return ResultadoPipelineTsne(
        coords_2d=coords_2d,
        coords_3d=coords_3d,
        etiquetas=etiquetas,
        n_clusters=n_clusters,
        perplexity=perplexity,
        n_sesiones=n_sesiones,
    )
