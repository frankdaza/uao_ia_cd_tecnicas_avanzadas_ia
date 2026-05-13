"""Recuperacion de documentos (MVP: BM25 a nivel archivo)."""

from src.legacy.retrieval.recuperador import (
    DocumentoRecuperado,
    RecuperacionVaciaError,
    RecuperadorBm25,
    RecuperadorDocumento,
    cargar_corpus,
    parsear_markdown,
    tokenizar,
)

__all__ = [
    "DocumentoRecuperado",
    "RecuperacionVaciaError",
    "RecuperadorBm25",
    "RecuperadorDocumento",
    "cargar_corpus",
    "parsear_markdown",
    "tokenizar",
]
