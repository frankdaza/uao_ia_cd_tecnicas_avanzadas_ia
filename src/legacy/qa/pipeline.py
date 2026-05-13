"""Pipeline Q&A: recuperación BM25, composición de mensajes y chat con Ollama u OpenAI."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from src.qa.cliente_ollama import ClienteOllama, ConfiguracionLlm
from src.qa.cliente_openai import (
    MODELOS_OPENAI_SOPORTADOS,
    ClienteOpenAi,
    ConfiguracionOpenai,
)
from src.qa.prompt import PROMPT_SISTEMA_DEFECTO, componer_mensajes_multi

from src.legacy.retrieval.recuperador import (
    DocumentoRecuperado,
    RecuperacionVaciaError,
    RecuperadorBm25,
    RecuperadorDocumento,
)

K_TOP_DOCUMENTOS: int = 3


@dataclass(frozen=True)
class FuenteBm25:
    """Metadatos de un documento recuperado (sin el cuerpo Markdown completo)."""

    ruta: Path
    titulo: str
    source_url: str
    score: float


def _fuentes_desde_documentos(
    documentos: list[DocumentoRecuperado],
) -> tuple[FuenteBm25, ...]:
    return tuple(
        FuenteBm25(
            ruta=d.ruta,
            titulo=d.titulo,
            source_url=d.source_url,
            score=d.score,
        )
        for d in documentos
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
    fuentes_bm25: tuple[FuenteBm25, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ContextoInferencia:
    """Una única pasada BM25 + ``componer_mensajes_multi`` para Ollama u OpenAI."""

    vacio: bool
    mensajes: list[dict[str, str]]
    documentos: tuple[DocumentoRecuperado, ...]
    prompt_sistema_usado: str


class PipelineQa:
    """Orquesta recuperador, prompt y clientes LLM (Ollama y opcionalmente OpenAI)."""

    def __init__(
        self,
        recuperador: RecuperadorDocumento,
        cliente: ClienteOllama,
        cliente_openai: ClienteOpenAi | None = None,
        prompt_sistema: str = PROMPT_SISTEMA_DEFECTO,
    ) -> None:
        self._recuperador = recuperador
        self._cliente = cliente
        self._cliente_openai = cliente_openai
        self._prompt_sistema = prompt_sistema

    @property
    def recuperador(self) -> RecuperadorDocumento:
        """Recuperador BM25; expuesto para tareas p. ej. :meth:`~RecuperadorDocumento.recargar`."""
        return self._recuperador

    @property
    def cliente_openai(self) -> ClienteOpenAi | None:
        """Cliente OpenAI si se construyó con uno (puede existir sin API key)."""
        return self._cliente_openai

    def preparar_contexto_inferencia(
        self,
        pregunta: str,
        prompt_sistema: str | None = None,
    ) -> ContextoInferencia:
        """
        Ejecuta BM25 y :func:`~src.qa.prompt.componer_mensajes_multi` una sola vez.

        Reutilizar el :class:`ContextoInferencia` retornado para Ollama y OpenAI
        sin volver a llamar al recuperador.
        """
        ps = self._prompt_sistema if prompt_sistema is None else prompt_sistema
        try:
            documentos = self._recuperador.buscar_top(
                pregunta, k=K_TOP_DOCUMENTOS
            )
        except RecuperacionVaciaError:
            return ContextoInferencia(
                vacio=True,
                mensajes=[],
                documentos=(),
                prompt_sistema_usado=ps,
            )
        lista = list(documentos)
        mensajes = componer_mensajes_multi(ps, lista, pregunta)
        return ContextoInferencia(
            vacio=False,
            mensajes=mensajes,
            documentos=tuple(lista),
            prompt_sistema_usado=ps,
        )

    def _latencia_desde(self, inicio: float) -> int:
        return int((time.perf_counter() - inicio) * 1000)

    def _respuesta_qa_bm25_vacio(
        self,
        prompt_sistema_usado: str,
        modelo_etiqueta: str,
        t_inicio: float,
    ) -> RespuestaQa:
        return RespuestaQa(
            texto="No tengo información suficiente",
            archivo_fuente=None,
            source_url="",
            titulo="",
            modelo=modelo_etiqueta,
            score_recuperacion=0.0,
            latencia_ms=self._latencia_desde(t_inicio),
            prompt_sistema_usado=prompt_sistema_usado,
            fuentes_bm25=(),
        )

    def _respuesta_qa_desde_contexto(
        self,
        ctx: ContextoInferencia,
        texto: str,
        modelo_etiqueta: str,
        t_inicio_llm: float,
    ) -> RespuestaQa:
        doc = ctx.documentos[0]
        return RespuestaQa(
            texto=texto,
            archivo_fuente=doc.ruta,
            source_url=doc.source_url,
            titulo=doc.titulo,
            modelo=modelo_etiqueta,
            score_recuperacion=doc.score,
            latencia_ms=self._latencia_desde(t_inicio_llm),
            prompt_sistema_usado=ctx.prompt_sistema_usado,
            fuentes_bm25=_fuentes_desde_documentos(list(ctx.documentos)),
        )

    def responder(
        self,
        pregunta: str,
        *,
        modelo: str | None = None,
        prompt_sistema: str | None = None,
        num_ctx: int | None = None,
    ) -> RespuestaQa:
        ps = self._prompt_sistema if prompt_sistema is None else prompt_sistema
        t_inicio = time.perf_counter()
        ctx = self.preparar_contexto_inferencia(pregunta, ps)
        if ctx.vacio:
            return self._respuesta_qa_bm25_vacio(
                ps,
                self._cliente.configuracion.modelo,
                t_inicio,
            )

        def _modelo_elegido() -> str:
            return (
                self._cliente.configuracion.modelo
                if modelo is None
                else modelo
            )

        mo = _modelo_elegido()
        t_llm = time.perf_counter()
        anterior: str | None = None
        if modelo is not None:
            anterior = self._cliente.configuracion.modelo
            self._cliente.configuracion.modelo = modelo
        try:
            texto = self._cliente.chat(ctx.mensajes, num_ctx=num_ctx)
        finally:
            if anterior is not None:
                self._cliente.configuracion.modelo = anterior

        return self._respuesta_qa_desde_contexto(ctx, texto, mo, t_llm)

    def responder_openai(
        self,
        pregunta: str,
        *,
        modelo_openai: str,
        prompt_sistema: str | None = None,
        max_completion_tokens: int | None = None,
        temperatura: float | None = None,
        top_p: float | None = None,
    ) -> RespuestaQa:
        """Misma recuperación y mensajes que Ollama; generación vía API OpenAI."""
        if self._cliente_openai is None:
            raise RuntimeError("Cliente OpenAI no configurado en el pipeline")
        ps = self._prompt_sistema if prompt_sistema is None else prompt_sistema
        t_inicio = time.perf_counter()
        ctx = self.preparar_contexto_inferencia(pregunta, ps)
        if ctx.vacio:
            return self._respuesta_qa_bm25_vacio(ps, modelo_openai, t_inicio)

        t_llm = time.perf_counter()
        texto = self._cliente_openai.chat(
            ctx.mensajes,
            modelo=modelo_openai,
            max_completion_tokens=max_completion_tokens,
            temperatura=temperatura,
            top_p=top_p,
        )
        return self._respuesta_qa_desde_contexto(
            ctx, texto, modelo_openai, t_llm
        )

    def responder_dual(
        self,
        pregunta: str,
        *,
        usar_ollama: bool,
        usar_openai: bool,
        modelo_ollama: str | None,
        modelo_openai: str | None,
        prompt_sistema: str | None = None,
        max_completion_tokens: int | None = None,
        num_ctx: int | None = None,
    ) -> tuple[RespuestaQa | None, RespuestaQa | None]:
        """
        Una sola pasada BM25 + composición; luego Ollama y/o OpenAI en **serie**
        (sin streaming simultáneo).
        """
        ps = self._prompt_sistema if prompt_sistema is None else prompt_sistema
        t0 = time.perf_counter()
        ctx = self.preparar_contexto_inferencia(pregunta, ps)

        if ctx.vacio:
            lat = self._latencia_desde(t0)
            mo = (
                modelo_ollama
                if modelo_ollama
                else self._cliente.configuracion.modelo
            )
            ma = (
                modelo_openai
                if modelo_openai
                else MODELOS_OPENAI_SOPORTADOS[0]
            )
            base = dict(
                texto="No tengo información suficiente",
                archivo_fuente=None,
                source_url="",
                titulo="",
                score_recuperacion=0.0,
                latencia_ms=lat,
                prompt_sistema_usado=ps,
                fuentes_bm25=(),
            )
            return (
                RespuestaQa(modelo=mo, **base) if usar_ollama else None,
                RespuestaQa(modelo=ma, **base) if usar_openai else None,
            )

        resultado_ollama: RespuestaQa | None = None
        resultado_openai: RespuestaQa | None = None

        if usar_ollama:
            assert modelo_ollama is not None
            t_ollama = time.perf_counter()
            anterior: str | None = None
            if modelo_ollama != self._cliente.configuracion.modelo:
                anterior = self._cliente.configuracion.modelo
                self._cliente.configuracion.modelo = modelo_ollama
            try:
                texto_o = self._cliente.chat(ctx.mensajes, num_ctx=num_ctx)
            finally:
                if anterior is not None:
                    self._cliente.configuracion.modelo = anterior
            resultado_ollama = self._respuesta_qa_desde_contexto(
                ctx, texto_o, modelo_ollama, t_ollama
            )

        if usar_openai:
            if self._cliente_openai is None:
                raise RuntimeError("Cliente OpenAI no configurado en el pipeline")
            assert modelo_openai is not None
            t_oai = time.perf_counter()
            texto_a = self._cliente_openai.chat(
                ctx.mensajes,
                modelo=modelo_openai,
                max_completion_tokens=max_completion_tokens,
                temperatura=None,
                top_p=None,
            )
            resultado_openai = self._respuesta_qa_desde_contexto(
                ctx, texto_a, modelo_openai, t_oai
            )

        return resultado_ollama, resultado_openai

    def stream_ollama_desde_contexto(
        self,
        ctx: ContextoInferencia,
        modelo_efectivo: str,
        t_llm: float,
        *,
        num_ctx: int | None = None,
    ) -> Iterator[tuple[str, RespuestaQa | None]]:
        """
        Una pasada BM25 ya resuelta en ``ctx``. Emite deltas y al final una
        ``RespuestaQa`` con metadatos (mismo contrato que :meth:`responder_stream`).
        """
        anterior: str | None = None
        if modelo_efectivo != self._cliente.configuracion.modelo:
            anterior = self._cliente.configuracion.modelo
            self._cliente.configuracion.modelo = modelo_efectivo
        acumulado = ""
        try:
            for delta in self._cliente.chat_stream(ctx.mensajes, num_ctx=num_ctx):
                acumulado += delta
                yield acumulado, None
        finally:
            if anterior is not None:
                self._cliente.configuracion.modelo = anterior

        documento = ctx.documentos[0]
        final = RespuestaQa(
            texto=acumulado,
            archivo_fuente=documento.ruta,
            source_url=documento.source_url,
            titulo=documento.titulo,
            modelo=modelo_efectivo,
            score_recuperacion=documento.score,
            latencia_ms=self._latencia_desde(t_llm),
            prompt_sistema_usado=ctx.prompt_sistema_usado,
            fuentes_bm25=_fuentes_desde_documentos(list(ctx.documentos)),
        )
        yield acumulado, final

    def stream_openai_desde_contexto(
        self,
        ctx: ContextoInferencia,
        modelo_openai: str,
        t_llm: float,
        *,
        max_completion_tokens: int | None = None,
        temperatura: float | None = None,
        top_p: float | None = None,
    ) -> Iterator[tuple[str, RespuestaQa | None]]:
        """Contexto BM25 ya resuelto; streaming vía cliente OpenAI."""
        if self._cliente_openai is None:
            raise RuntimeError("Cliente OpenAI no configurado en el pipeline")
        acumulado = ""
        for delta in self._cliente_openai.chat_stream(
            ctx.mensajes,
            modelo=modelo_openai,
            max_completion_tokens=max_completion_tokens,
            temperatura=temperatura,
            top_p=top_p,
        ):
            acumulado += delta
            yield acumulado, None

        yield acumulado, self._respuesta_qa_desde_contexto(
            ctx,
            acumulado,
            modelo_openai,
            t_llm,
        )

    def responder_openai_stream(
        self,
        pregunta: str,
        *,
        modelo_openai: str,
        prompt_sistema: str | None = None,
        max_completion_tokens: int | None = None,
        temperatura: float | None = None,
        top_p: float | None = None,
    ) -> Iterator[tuple[str, RespuestaQa | None]]:
        """Analogo a :meth:`responder_stream` pero con la API de OpenAI."""
        if self._cliente_openai is None:
            raise RuntimeError("Cliente OpenAI no configurado en el pipeline")

        ps = self._prompt_sistema if prompt_sistema is None else prompt_sistema
        t_inicio = time.perf_counter()

        def _latencia_ms() -> int:
            return int((time.perf_counter() - t_inicio) * 1000)

        ctx = self.preparar_contexto_inferencia(pregunta, ps)
        if ctx.vacio:
            texto_vacio = "No tengo información suficiente"
            final = RespuestaQa(
                texto=texto_vacio,
                archivo_fuente=None,
                source_url="",
                titulo="",
                modelo=modelo_openai,
                score_recuperacion=0.0,
                latencia_ms=_latencia_ms(),
                prompt_sistema_usado=ps,
            )
            yield texto_vacio, final
            return

        t_llm = time.perf_counter()
        yield from self.stream_openai_desde_contexto(
            ctx,
            modelo_openai,
            t_llm,
            max_completion_tokens=max_completion_tokens,
            temperatura=temperatura,
            top_p=top_p,
        )

    def responder_stream(
        self,
        pregunta: str,
        *,
        modelo: str | None = None,
        prompt_sistema: str | None = None,
        num_ctx: int | None = None,
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

        ctx = self.preparar_contexto_inferencia(pregunta, ps)
        if ctx.vacio:
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

        t_llm = time.perf_counter()
        yield from self.stream_ollama_desde_contexto(
            ctx,
            modelo_efectivo,
            t_llm,
            num_ctx=num_ctx,
        )


def construir_pipeline_por_defecto(
    directorio_markdown: Path = Path("data/markdown/valledellili-org"),
) -> PipelineQa:
    """
    Crea un pipeline con BM25 sobre ``directorio_markdown``, Ollama y cliente
    OpenAI (sin clave no falla hasta invocar la API).
    """
    recuperador = RecuperadorBm25(directorio_markdown)
    cliente = ClienteOllama(ConfiguracionLlm.desde_variables_entorno())
    cliente_openai = ClienteOpenAi(ConfiguracionOpenai.desde_variables_entorno())
    return PipelineQa(recuperador, cliente, cliente_openai)


__all__ = [
    "ContextoInferencia",
    "FuenteBm25",
    "K_TOP_DOCUMENTOS",
    "PROMPT_SISTEMA_DEFECTO",
    "PipelineQa",
    "RespuestaQa",
    "construir_pipeline_por_defecto",
]
