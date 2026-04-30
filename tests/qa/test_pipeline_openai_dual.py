"""Pipeline: OpenAI y modo dual sin red (mock)."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.qa.cliente_ollama import ClienteOllama, ConfiguracionLlm, MODELO_LLAMA_3_1_8B
from src.qa.cliente_openai import (
    MODELOS_OPENAI_SOPORTADOS,
    ClienteOpenAi,
)
from src.qa.pipeline import PipelineQa
from src.retrieval.recuperador import RecuperadorBm25


def test_responder_openai_usa_mismos_mensajes_que_ollama_mock(
    dir_fixtures_markdown,
) -> None:
    recuperador = RecuperadorBm25(dir_fixtures_markdown)
    cliente_o = MagicMock(spec=ClienteOllama)
    cliente_o.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente_o.chat.return_value = "desde ollama"
    cliente_oa = MagicMock(spec=ClienteOpenAi)
    cliente_oa.chat.return_value = "desde openai"

    pipe = PipelineQa(recuperador, cliente_o, cliente_oa)

    pipe.responder_openai(
        "¿Cuáles son los servicios de cardiología?",
        modelo_openai="gpt-4o-mini",
    )

    cliente_oa.chat.assert_called_once()
    msg_oa = cliente_oa.chat.call_args[0][0]

    cliente_o.chat.reset_mock()

    pipe.responder(
        "¿Cuáles son los servicios de cardiología?",
        modelo=MODELO_LLAMA_3_1_8B,
    )
    cliente_o.chat.assert_called_once()
    msg_o = cliente_o.chat.call_args[0][0]

    assert msg_o == msg_oa


class _PipelineConteoPrepara(PipelineQa):
    """Cuenta invocaciones a :meth:`~PipelineQa.preparar_contexto_inferencia`."""

    def __init__(self, *args, **kwargs) -> None:
        self._prep_llamadas: list[int] = []
        super().__init__(*args, **kwargs)

    def preparar_contexto_inferencia(
        self,
        pregunta: str,
        prompt_sistema: str | None = None,
    ):
        self._prep_llamadas.append(1)
        return super().preparar_contexto_inferencia(pregunta, prompt_sistema)


def test_responder_dual_una_sola_llamada_a_preparar_contexto(dir_fixtures_markdown) -> None:


    recuperador = RecuperadorBm25(dir_fixtures_markdown)
    cliente_o = MagicMock(spec=ClienteOllama)
    cliente_o.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente_o.chat.return_value = "respuesta-o"
    cliente_oa = MagicMock(spec=ClienteOpenAi)
    cliente_oa.chat.return_value = "respuesta-oa"

    pipe = _PipelineConteoPrepara(recuperador, cliente_o, cliente_oa)
    pipe.responder_dual(
        "¿Cuáles son los servicios de cardiología?",
        usar_ollama=True,
        usar_openai=True,
        modelo_ollama=MODELO_LLAMA_3_1_8B,
        modelo_openai=MODELOS_OPENAI_SOPORTADOS[1],
        prompt_sistema=None,
    )

    assert len(pipe._prep_llamadas) == 1


def test_responder_openai_stream_usa_chat_stream(dir_fixtures_markdown) -> None:
    recuperador = RecuperadorBm25(dir_fixtures_markdown)
    cliente_o = MagicMock(spec=ClienteOllama)
    cliente_o.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente_oa = MagicMock(spec=ClienteOpenAi)
    cliente_oa.chat_stream.return_value = iter(["a", "b", "c"])

    pipe = PipelineQa(recuperador, cliente_o, cliente_oa)
    resultados: list[tuple[str, object | None]] = list(
        pipe.responder_openai_stream(
            "¿Cuáles son los servicios de cardiología?",
            modelo_openai="gpt-4o-mini",
        )
    )

    assert resultados[-1][1] is not None
    assert resultados[-1][0] == "abc"
    parciales_sin_final = [t for t, rq in resultados if rq is None]
    assert parciales_sin_final[-1] == "abc"
    cliente_oa.chat_stream.assert_called_once()


def test_responder_openai_propaga_max_completion_tokens(dir_fixtures_markdown) -> None:
    recuperador = RecuperadorBm25(dir_fixtures_markdown)
    cliente_o = MagicMock(spec=ClienteOllama)
    cliente_o.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente_oa = MagicMock(spec=ClienteOpenAi)
    cliente_oa.chat.return_value = "ok"

    pipe = PipelineQa(recuperador, cliente_o, cliente_oa)
    pipe.responder_openai(
        "¿Cuáles son los servicios de cardiología?",
        modelo_openai="gpt-4o-mini",
        max_completion_tokens=512,
    )
    assert cliente_oa.chat.call_args.kwargs["max_completion_tokens"] == 512
