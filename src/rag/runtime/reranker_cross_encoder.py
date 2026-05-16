"""
Reranking de candidatos RAG con **cross-encoder** (``sentence_transformers.CrossEncoder``).

Contexto
--------
La recuperación densa (embeddings + Qdrant) devuelve textos ordenados por similitud coseno
entre vectores de consulta y de fragmentos. Un cross-encoder vuelve a evaluar cada par
**(consulta, fragmento)** en un solo modelo secuencial, lo que suele correlacionar mejor
con relevancia que la mera proximidad vectorial, a costa de mayor latencia y RAM.

Este módulo no orquesta el pipeline completo: ``RecuperadorDenso`` (``src/rag/runtime/recuperador_denso.py``)
instancia ``RerankerCrossEncoder`` cuando el reranker está habilitado en configuración. El
lifespan de FastAPI puede hacer *warmup* del modelo al arrancar (ver ``src/api/main.py``).

Dependencia
-----------
Requiere el paquete ``sentence-transformers``. Si no está instalado, la primera carga del
encoder lanza ``RuntimeError`` con el mensaje definido en ``_MENSAJE_SIN_ST``.

Carga de modelos y concurrencia
-------------------------------
- **Carga perezosa**: el peso del modelo no se descarga hasta la primera llamada a ``puntuar``
  (o hasta el warmup en lifespan).
- **Singleton por id de modelo**: dentro del proceso, todas las instancias de
  ``RerankerCrossEncoder`` que comparten el mismo string ``modelo`` reutilizan el mismo
  objeto ``CrossEncoder`` en memoria (diccionario global ``_modelos_cargados`` protegido
  con ``threading.Lock``).
- **Tamaño de lote**: ``puntuar`` delega en ``CrossEncoder.predict`` con ``batch_size``;
  el valor por defecto local es ``_BATCH_SIZE_PREDETERMINADO`` (16), alineado con
  ``Configuracion.rag_reranker_batch_size`` cuando el llamador pasa ese valor.

Salida de ``puntuar``
---------------------
Devuelve una lista de la misma longitud que ``textos_candidatos``. Cada elemento es un
``float`` (score; mayor = más relevante) o ``None`` si el modelo devolvió un valor no
numérico, no finito (NaN/inf) o hubo desajuste de cardinalidad; el recuperador suele
filtrar ``None`` antes de ordenar. Los problemas se registran con ``logging.warning``.
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
    """Importa ``CrossEncoder`` de forma diferida; falla con mensaje operable si falta el paquete."""
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise RuntimeError(_MENSAJE_SIN_ST) from exc
    return CrossEncoder


class RerankerCrossEncoder:
    """
    Envoltorio mínimo sobre ``sentence_transformers.CrossEncoder``.

    Responsabilidades: validar el identificador de modelo, cargar el encoder bajo bloqueo
    compartido, reutilizar instancias ya cargadas y exponer ``puntuar`` para pares
    (consulta, candidato) con procesamiento por lotes y tolerancia a salidas anómalas
    del modelo.
    """

    def __init__(self, modelo: str) -> None:
        """
        Args:
            modelo: Nombre o ruta del modelo cross-encoder reconocida por
                ``sentence_transformers`` (p. ej. un id de Hugging Face). No puede ser
                cadena vacía ni solo espacios.
        """
        self._modelo = str(modelo).strip()
        if not self._modelo:
            raise ValueError("modelo del reranker no puede quedar vacio")
        self._encoder: object | None = None

    def _obtener_encoder(self) -> object:
        """
        Devuelve la instancia ``CrossEncoder``, creándola o tomándola del caché global.

        Doble comprobación bajo ``_lock`` para evitar cargas duplicadas del mismo
        ``modelo`` en hilos concurrentes.
        """
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
        Calcula un score de relevancia por candidato respecto a la consulta.

        Construye pares ``[consulta, texto]`` y llama a ``CrossEncoder.predict`` con el
        ``batch_size`` indicado (o el predeterminado del módulo si ``batch_size`` es
        ``None``).

        Args:
            consulta: Pregunta o texto de consulta del usuario (primer elemento de cada par).
            textos_candidatos: Fragmentos recuperados por RAG u otra fuente, en el orden
                deseado para alinear índices con la salida.
            batch_size: Tamaño de lote para ``predict``. ``None`` usa
                ``_BATCH_SIZE_PREDETERMINADO`` (16).

        Returns:
            Lista paralela a ``textos_candidatos``: ``float`` donde un valor **mayor**
            suele indicar **mayor relevancia** frente a la consulta (convención típica de
            cross-encoders de ranking), o ``None`` donde el resultado no sea un número
            finito, con ``logging.warning`` según el caso.
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
        """
        Vacía el caché global de modelos cargados.

        Pensado únicamente para pruebas (p. ej. ``tests/rag/test_reranker_cross_encoder.py``)
        para aislar casos que mockean ``CrossEncoder`` o verifican una sola carga por modelo.
        No usar en producción salvo que se entienda el coste de volver a cargar pesos.
        """
        with _lock:
            _modelos_cargados.clear()
