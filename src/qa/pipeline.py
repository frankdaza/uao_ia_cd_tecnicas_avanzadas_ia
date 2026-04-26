"""Pipeline Q&A: recuperación BM25, composición de mensajes y chat con Ollama."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.qa.cliente_ollama import ClienteOllama, ConfiguracionLlm
from src.qa.prompt import PROMPT_SISTEMA_DEFECTO, componer_mensajes
from src.retrieval.recuperador import (
    RecuperacionVaciaError,
    RecuperadorBm25,
    RecuperadorDocumento,
)


@dataclass(frozen=True)
class RespuestaQa:
    """Resultado de una consulta con metadatos de trazabilidad."""

    texto: str
    archivo_fuente: Path | None
    source_url: str
    titulo: str
    modelo: str
    score_recuperacion: float
    latencia_ms: int
    prompt_sistema_usado: str


class PipelineQa:
    """Orquesta recuperador, prompt y cliente LLM (Ollama)."""

    def __init__(
        self,
        recuperador: RecuperadorDocumento,
        cliente: ClienteOllama,
        prompt_sistema: str = PROMPT_SISTEMA_DEFECTO,
    ) -> None:
        self._recuperador = recuperador
        self._cliente = cliente
        self._prompt_sistema = prompt_sistema

    @property
    def recuperador(self) -> RecuperadorDocumento:
        """Recuperador BM25; expuesto para tareas p. ej. :meth:`~RecuperadorDocumento.recargar`."""
        return self._recuperador

    def responder(
        self,
        pregunta: str,
        *,
        modelo: str | None = None,
        prompt_sistema: str | None = None,
    ) -> RespuestaQa:
        ps = self._prompt_sistema if prompt_sistema is None else prompt_sistema
        t_inicio = time.perf_counter()

        def _latencia_ms() -> int:
            return int((time.perf_counter() - t_inicio) * 1000)

        def _modelo_elegido() -> str:
            return (
                self._cliente.configuracion.modelo
                if modelo is None
                else modelo
            )

        try:
            documento = self._recuperador.buscar(pregunta)
        except RecuperacionVaciaError:
            return RespuestaQa(
                texto="No tengo información suficiente",
                archivo_fuente=None,
                source_url="",
                titulo="",
                modelo=self._cliente.configuracion.modelo,
                score_recuperacion=0.0,
                latencia_ms=_latencia_ms(),
                prompt_sistema_usado=ps,
            )

        metadata: dict[str, Any] = {
            "source_url": documento.source_url,
            "titulo": documento.titulo,
        }
        mensajes = componer_mensajes(
            ps,
            documento.contenido,
            pregunta,
            metadata_documento=metadata,
        )
        mo = _modelo_elegido()
        anterior: str | None = None
        if modelo is not None:
            anterior = self._cliente.configuracion.modelo
            self._cliente.configuracion.modelo = modelo
        try:
            texto = self._cliente.chat(mensajes)
        finally:
            if anterior is not None:
                self._cliente.configuracion.modelo = anterior

        return RespuestaQa(
            texto=texto,
            archivo_fuente=documento.ruta,
            source_url=documento.source_url,
            titulo=documento.titulo,
            modelo=mo,
            score_recuperacion=documento.score,
            latencia_ms=_latencia_ms(),
            prompt_sistema_usado=ps,
        )


    def responder_stream(
        self,
        pregunta: str,
        *,
        modelo: str | None = None,
        prompt_sistema: str | None = None,
    ) -> Iterator[tuple[str, RespuestaQa | None]]:
        """Genera tuplas ``(texto_acumulado, RespuestaQa | None)``.

        Mientras llegan tokens, emite el texto acumulado con ``None`` en la
        segunda posicion. Al finalizar, emite una ultima tupla con el texto
        completo y la ``RespuestaQa`` con metadatos de trazabilidad.
        """
        ps = self._prompt_sistema if prompt_sistema is None else prompt_sistema
        t_inicio = time.perf_counter()

        def _latencia_ms() -> int:
            return int((time.perf_counter() - t_inicio) * 1000)

        modelo_efectivo = (
            self._cliente.configuracion.modelo if modelo is None else modelo
        )

        try:
            documento = self._recuperador.buscar(pregunta)
        except RecuperacionVaciaError:
            texto_vacio = "No tengo información suficiente"
            final = RespuestaQa(
                texto=texto_vacio,
                archivo_fuente=None,
                source_url="",
                titulo="",
                modelo=self._cliente.configuracion.modelo,
                score_recuperacion=0.0,
                latencia_ms=_latencia_ms(),
                prompt_sistema_usado=ps,
            )
            yield texto_vacio, final
            return

        metadata: dict[str, Any] = {
            "source_url": documento.source_url,
            "titulo": documento.titulo,
        }
        mensajes = componer_mensajes(
            ps,
            documento.contenido,
            pregunta,
            metadata_documento=metadata,
        )

        anterior: str | None = None
        if modelo is not None:
            anterior = self._cliente.configuracion.modelo
            self._cliente.configuracion.modelo = modelo
        acumulado = ""
        try:
            for delta in self._cliente.chat_stream(mensajes):
                acumulado += delta
                yield acumulado, None
        finally:
            if anterior is not None:
                self._cliente.configuracion.modelo = anterior

        final = RespuestaQa(
            texto=acumulado,
            archivo_fuente=documento.ruta,
            source_url=documento.source_url,
            titulo=documento.titulo,
            modelo=modelo_efectivo,
            score_recuperacion=documento.score,
            latencia_ms=_latencia_ms(),
            prompt_sistema_usado=ps,
        )
        yield acumulado, final


def construir_pipeline_por_defecto(
    directorio_markdown: Path = Path("data/markdown/valledellili-org"),
) -> PipelineQa:
    """
    Crea un pipeline con BM25 sobre ``directorio_markdown`` y Ollama según
    variables de entorno (p. ej. ``OLLAMA_BASE_URL``, ``MODELO_LLM_DEFECTO``).
    """
    recuperador = RecuperadorBm25(directorio_markdown)
    cliente = ClienteOllama(ConfiguracionLlm.desde_variables_entorno())
    return PipelineQa(recuperador, cliente)


__all__ = [
    "PROMPT_SISTEMA_DEFECTO",
    "PipelineQa",
    "RespuestaQa",
    "construir_pipeline_por_defecto",
]
