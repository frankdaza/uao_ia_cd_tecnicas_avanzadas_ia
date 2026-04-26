# MVP fase 1: BM25 a nivel archivo. NO usar embeddings/chunking aquí.
# Prohibido en este módulo: sklearn, faiss, chromadb, qdrant_client,
# langchain.embeddings, llama_index.embeddings, sentence_transformers, chunking.

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np
import yaml
from rank_bm25 import BM25Okapi

_STOPWORDS_ES: frozenset[str] = frozenset(
    {
        "de",
        "la",
        "el",
        "en",
        "y",
        "que",
        "los",
        "las",
        "del",
        "un",
        "una",
        "por",
        "con",
        "para",
        "se",
        "su",
        "es",
        "al",
        "lo",
        "a",
        "o",
    }
)


@dataclass(frozen=True)
class DocumentoRecuperado:
    ruta: Path
    titulo: str
    source_url: str
    contenido: str
    score: float


class RecuperacionVaciaError(Exception):
    """
    Ningun documento obtuvo relevancia BM25 > 0 para los terminos de la pregunta.
    """


@runtime_checkable
class RecuperadorDocumento(Protocol):
    def buscar(self, pregunta: str) -> DocumentoRecuperado: ...

    def recargar(self) -> None: ...


def _quitar_marcas_combinantes(texto: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", texto)
        if unicodedata.category(c) != "Mn"
    )


def tokenizar(texto: str) -> list[str]:
    """
    Minusculas, sin tildes, palabras (regex ``\\\\w+``), longitud >= 2,
    sin stopwords basicas en espanol.
    """
    t = _quitar_marcas_combinantes(texto)
    t = t.lower()
    out: list[str] = []
    for w in re.findall(r"\w+", t, flags=re.UNICODE):
        if len(w) < 2:
            continue
        if w in _STOPWORDS_ES:
            continue
        out.append(w)
    return out


def parsear_markdown(texto: str) -> tuple[dict[str, Any], str]:
    """
    Separa front matter YAML del cuerpo (texto tras el segundo ``---`` en linea).
    Si no hay front matter valido, devuelve ``({}, texto completo)``.
    """
    t = texto.lstrip("\ufeff")
    # Apertura ---, bloque YAML, cierre --- en su propia linea, luego cuerpo.
    m = re.match(
        r"^---[ \t]*\r?\n(.*?)^---[ \t]*\r?\n?(.*)\Z",
        t,
        flags=re.DOTALL | re.MULTILINE,
    )
    if not m:
        return {}, t
    yml, cuerpo = m.group(1), m.group(2)
    try:
        meta = yaml.safe_load(yml) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, cuerpo


def texto_indexable(front: dict[str, Any], cuerpo: str) -> str:
    """Titulo (front) + cuerpo; el front en si no se indexa salvo el titulo."""
    tit = str(front.get("titulo", "") or "")
    return f"{tit}\n{cuerpo}" if tit else cuerpo


def cargar_corpus(
    directorio_markdown: Path,
    glob: str = "**/*.md",
) -> list[tuple[Path, dict[str, Any], str, list[str]]]:
    """
    Lee cada ``.md``, parsea front matter y devuelve tuplas
    ``(ruta, front_matter, cuerpo, tokens)`` para el texto indexable.
    """
    base = directorio_markdown.resolve()
    salida: list[tuple[Path, dict[str, Any], str, list[str]]] = []
    for ruta in sorted(base.glob(glob), key=lambda p: p.as_posix().lower()):
        if not ruta.is_file():
            continue
        raw = ruta.read_text(encoding="utf-8", errors="replace")
        front, cuerpo = parsear_markdown(raw)
        idx = texto_indexable(front, cuerpo)
        salida.append((ruta, front, cuerpo, tokenizar(idx)))
    return salida


class RecuperadorBm25:
    def __init__(
        self,
        directorio_markdown: Path,
        glob: str = "**/*.md",
    ) -> None:
        self._directorio = directorio_markdown
        self._glob = glob
        self._rutas: list[Path] = []
        self._titulos: list[str] = []
        self._urls: list[str] = []
        self._cuerpos: list[str] = []
        self._token_docs: list[list[str]] = []
        self._bm25: BM25Okapi | None = None
        self._reindexar()

    def _reindexar(self) -> None:
        cargado = cargar_corpus(self._directorio, self._glob)
        if not cargado:
            msg = f"No se encontraron archivos Markdown en {self._directorio!r} (glob {self._glob!r})."
            raise ValueError(msg)
        self._rutas = []
        self._titulos = []
        self._urls = []
        self._cuerpos = []
        self._token_docs = []
        for ruta, front, cuerpo, tokens in cargado:
            self._rutas.append(ruta)
            self._titulos.append(str(front.get("titulo", "") or ""))
            self._urls.append(str(front.get("source_url", "") or ""))
            self._cuerpos.append(cuerpo)
            self._token_docs.append(tokens)
        self._bm25 = BM25Okapi(self._token_docs)

    def buscar(self, pregunta: str) -> DocumentoRecuperado:
        if self._bm25 is None or not self._rutas:
            raise RecuperacionVaciaError("Indice BM25 no disponible.")
        toks = tokenizar(pregunta)
        if not toks:
            raise RecuperacionVaciaError("La pregunta no produjo terminos tras tokenizar.")
        scores = self._bm25.get_scores(toks)
        arr = np.asarray(scores, dtype=np.float64)
        if not np.any(arr > 0):
            raise RecuperacionVaciaError(
                "Ningun documento tuvo score BM25 > 0 para esta pregunta."
            )
        i = int(np.argmax(arr))
        return DocumentoRecuperado(
            ruta=self._rutas[i],
            titulo=self._titulos[i],
            source_url=self._urls[i],
            contenido=self._cuerpos[i],
            score=float(arr[i]),
        )

    def recargar(self) -> None:
        self._reindexar()
