"""
Reranking con cross-encoder (sentence-transformers), carga perezosa y singleton por modelo.
"""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_modelos_cargados: dict[str, object] = {}

_MENSAJE_SIN_ST = "Instala con: uv add sentence-transformers"


def _importar_cross_encoder():
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise RuntimeError(_MENSAJE_SIN_ST) from exc
    return CrossEncoder


class RerankerCrossEncoder:
    """
    Envoltorio minimo sobre ``CrossEncoder`` con carga perezosa thread-safe.

    El modelo se comparte por ``modelo`` dentro del proceso (un singleton por id).
    """

    def __init__(self, modelo: str) -> None:
        self._modelo = str(modelo).strip()
        if not self._modelo:
            raise ValueError("modelo del reranker no puede quedar vacio")
        self._encoder: object | None = None

    def _obtener_encoder(self) -> object:
        if self._encoder is not None:
            return self._encoder
        with _lock:
            if self._modelo in _modelos_cargados:
                self._encoder = _modelos_cargados[self._modelo]
                return self._encoder
            CrossEncoder = _importar_cross_encoder()
            logger.info("Cargando cross-encoder RAG: %s", self._modelo)
            enc = CrossEncoder(self._modelo)
            _modelos_cargados[self._modelo] = enc
            self._encoder = enc
            return self._encoder

    def puntuar(self, consulta: str, textos_candidatos: list[str]) -> list[float]:
        """
        Devuelve un score por cada texto (mayor = mas relevante frente a ``consulta``).

        Usa ``CrossEncoder.predict`` sobre pares (consulta, texto).
        """
        if not textos_candidatos:
            return []
        enc = self._obtener_encoder()
        pares = [[consulta, t] for t in textos_candidatos]
        raw = enc.predict(pares)  # type: ignore[union-attr]
        salida: list[float] = []
        for x in raw:
            try:
                salida.append(float(x))
            except (TypeError, ValueError):
                salida.append(0.0)
        return salida

    @staticmethod
    def reiniciar_singletons_prueba() -> None:
        """Solo para tests: vacia modelos cacheados en memoria."""
        with _lock:
            _modelos_cargados.clear()
