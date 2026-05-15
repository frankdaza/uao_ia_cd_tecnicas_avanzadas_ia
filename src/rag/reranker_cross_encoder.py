"""
Reranking con cross-encoder (sentence-transformers), carga perezosa y singleton por modelo.
"""

from __future__ import annotations

import logging
import math
import threading

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_modelos_cargados: dict[str, object] = {}

_MENSAJE_SIN_ST = "Instala con: uv add sentence-transformers"

# Coincide con el default de ``Configuracion.rag_reranker_batch_size`` si no se pasa explicito.
_BATCH_SIZE_PREDETERMINADO: int = 16


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

    def puntuar(
        self,
        consulta: str,
        textos_candidatos: list[str],
        *,
        batch_size: int | None = None,
    ) -> list[float | None]:
        """
        Devuelve un score por cada texto (mayor = mas relevante frente a ``consulta``).

        Usa ``CrossEncoder.predict`` sobre pares (consulta, texto) con ``batch_size`` acotado.

        Si un valor devuelto por el modelo no es un ``float`` finito utilizable, se deja
        ``None`` en esa posicion (misma longitud que ``textos_candidatos``), se descarta
        el candidato para ordenacion y se registra un ``warning`` con el indice.
        """
        if not textos_candidatos:
            return []
        enc = self._obtener_encoder()
        pares = [[consulta, t] for t in textos_candidatos]
        bs = int(batch_size) if batch_size is not None else _BATCH_SIZE_PREDETERMINADO
        raw = enc.predict(pares, batch_size=bs)  # type: ignore[union-attr]
        n = len(textos_candidatos)
        salida: list[float | None] = [None] * n
        try:
            iterable = list(raw)
        except TypeError:
            iterable = [raw]
        if len(iterable) != n:
            logger.warning(
                "reranker.predict_cardinalidad_inesperada esperados=%s recibidos=%s",
                n,
                len(iterable),
            )
        for i in range(min(n, len(iterable))):
            x = iterable[i]
            try:
                val = float(x)
            except (TypeError, ValueError):
                logger.warning(
                    "reranker.score_no_numerico indice=%s tipo=%s",
                    i,
                    type(x).__name__,
                )
                continue
            if math.isnan(val) or math.isinf(val):
                logger.warning("reranker.score_no_finito indice=%s valor=%r", i, val)
                continue
            salida[i] = val
        return salida

    @staticmethod
    def reiniciar_singletons_prueba() -> None:
        """Solo para tests: vacia modelos cacheados en memoria."""
        with _lock:
            _modelos_cargados.clear()
