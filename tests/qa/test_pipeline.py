"""Pruebas del pipeline Q&A (recuperador + prompt + cliente Ollama)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import responses

from src.qa.cliente_ollama import (
    ClienteOllama,
    ConfiguracionLlm,
    ModeloNoDisponibleError,
    OllamaNoAccesibleError,
    MODELO_LLAMA_3_1_8B,
)
from src.legacy.qa.pipeline import PipelineQa, construir_pipeline_por_defecto
from src.legacy.retrieval.recuperador import RecuperacionVaciaError, RecuperadorBm25
from src.qa.prompt import PROMPT_SISTEMA_DEFECTO

pytestmark = pytest.mark.legacy_bm25


def test_pipeline_responde_pregunta_valida(dir_fixtures_markdown: Path) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    cliente = MagicMock(spec=ClienteOllama)
    cliente.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente.chat.return_value = "Respuesta simulada del modelo"

    pipe = PipelineQa(recu, cliente)  # type: ignore[arg-type]
    r = pipe.responder("¿Cuáles son los servicios de cardiología?")

    assert r.texto == "Respuesta simulada del modelo"
    assert r.archivo_fuente is not None
    assert r.archivo_fuente.name == "servicios-cardiologia.md"
    assert r.score_recuperacion > 0.0
    assert r.modelo == MODELO_LLAMA_3_1_8B
    assert r.latencia_ms >= 0
    assert r.prompt_sistema_usado == PROMPT_SISTEMA_DEFECTO
    assert len(r.fuentes_bm25) >= 1
    assert r.fuentes_bm25[0].ruta == r.archivo_fuente
    cliente.chat.assert_called_once()
    (mensajes,) = cliente.chat.call_args[0]
    assert len(mensajes) == 2
    assert mensajes[0]["role"] == "system"
    assert "[DOCUMENTO 1]" in mensajes[0]["content"]
    assert "CONTEXTO (" in mensajes[0]["content"]
    assert mensajes[1]["content"] == "¿Cuáles son los servicios de cardiología?"


def test_pipeline_recuperacion_vacia() -> None:
    recu = MagicMock()
    recu.buscar_top.side_effect = RecuperacionVaciaError("vacio de prueba")
    cliente = MagicMock(spec=ClienteOllama)
    cliente.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )

    pipe = PipelineQa(recu, cliente)  # type: ignore[arg-type]
    r = pipe.responder("xyz no indexado")

    assert r.texto == "No tengo información suficiente"
    assert r.archivo_fuente is None
    assert r.fuentes_bm25 == ()
    cliente.chat.assert_not_called()


def test_pipeline_mensaje_sistema_incluye_tres_documentos_consulta_amplia(
    dir_fixtures_markdown: Path,
) -> None:
    """Smoke: pregunta amplia recupera hasta K_TOP documentos BM25."""
    recu = RecuperadorBm25(dir_fixtures_markdown)
    cliente = MagicMock(spec=ClienteOllama)
    cliente.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente.chat.return_value = "ok"

    pipe = PipelineQa(recu, cliente)  # type: ignore[arg-type]
    pregunta = (
        "fundacion servicios cardiologia pediatria contacto historia lineas region"
    )
    r = pipe.responder(pregunta)
    assert len(r.fuentes_bm25) == 3

    (mensajes,) = cliente.chat.call_args[0]
    sistema = mensajes[0]["content"]
    assert "[DOCUMENTO 1]" in sistema
    assert "[DOCUMENTO 3]" in sistema


def test_pipeline_propaga_errores_ollama(dir_fixtures_markdown: Path) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    cliente = MagicMock(spec=ClienteOllama)
    cliente.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente.chat.side_effect = OllamaNoAccesibleError("no hay servidor")

    pipe = PipelineQa(recu, cliente)  # type: ignore[arg-type]
    with pytest.raises(OllamaNoAccesibleError, match="no hay servidor"):
        pipe.responder("¿Cuáles son los servicios de cardiología?")


def test_pipeline_propaga_modelo_no_disponible(
    dir_fixtures_markdown: Path,
) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    cliente = MagicMock(spec=ClienteOllama)
    cliente.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente.chat.side_effect = ModeloNoDisponibleError("falta modelo")

    pipe = PipelineQa(recu, cliente)  # type: ignore[arg-type]
    with pytest.raises(ModeloNoDisponibleError, match="falta modelo"):
        pipe.responder("¿Cuáles son los servicios de cardiología?")


def test_pipeline_acepta_prompt_override(dir_fixtures_markdown: Path) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    cliente = MagicMock(spec=ClienteOllama)
    cfg = ConfiguracionLlm(base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B)
    cliente.configuracion = cfg
    cliente.chat.return_value = "ok"

    pipe = PipelineQa(recu, cliente)  # type: ignore[arg-type]
    r = pipe.responder(
        "¿Cuáles son los servicios de cardiología?",
        prompt_sistema="SISTEMA_CUSTOM_UNICO",
    )
    (mensajes,) = cliente.chat.call_args[0]
    assert "SISTEMA_CUSTOM_UNICO" in mensajes[0]["content"]
    assert r.prompt_sistema_usado == "SISTEMA_CUSTOM_UNICO"


@responses.activate
def test_pipeline_modelo_override(dir_fixtures_markdown: Path) -> None:
    responses.add(
        responses.POST,
        "http://ollama.test/api/chat",
        json={"message": {"content": "ok gemma"}},
        status=200,
    )
    cfg = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    recu = RecuperadorBm25(dir_fixtures_markdown)
    cliente = ClienteOllama(cfg)
    assert cfg.modelo == MODELO_LLAMA_3_1_8B

    pipe = PipelineQa(recu, cliente)
    r = pipe.responder(
        "¿Cuáles son los servicios de cardiología?",
        modelo="gemma4:e2b",
    )

    cuerpo = json.loads(responses.calls[0].request.body)
    assert cuerpo["model"] == "gemma4:e2b"
    assert r.modelo == "gemma4:e2b"
    assert r.texto == "ok gemma"
    assert cfg.modelo == MODELO_LLAMA_3_1_8B, "el cliente debe volver al modelo por defecto"


def test_responder_stream_concatena_y_devuelve_metadatos(
    dir_fixtures_markdown: Path,
) -> None:
    recu = RecuperadorBm25(dir_fixtures_markdown)
    cliente = MagicMock(spec=ClienteOllama)
    cliente.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )
    cliente.chat_stream.return_value = iter(["Hola ", "parcero", "!"])

    pipe = PipelineQa(recu, cliente)  # type: ignore[arg-type]
    eventos = list(
        pipe.responder_stream("¿Cuáles son los servicios de cardiología?")
    )

    parciales = [texto for texto, final in eventos if final is None]
    assert parciales == ["Hola ", "Hola parcero", "Hola parcero!"]

    finales = [final for _texto, final in eventos if final is not None]
    assert len(finales) == 1
    final = finales[0]
    assert final.texto == "Hola parcero!"
    assert final.archivo_fuente is not None
    assert final.archivo_fuente.name == "servicios-cardiologia.md"
    assert final.score_recuperacion > 0.0
    assert len(final.fuentes_bm25) >= 1
    assert final.modelo == MODELO_LLAMA_3_1_8B
    assert final.latencia_ms >= 0


def test_responder_stream_recuperacion_vacia() -> None:
    recu = MagicMock()
    recu.buscar_top.side_effect = RecuperacionVaciaError("vacio")
    cliente = MagicMock(spec=ClienteOllama)
    cliente.configuracion = ConfiguracionLlm(
        base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B
    )

    pipe = PipelineQa(recu, cliente)  # type: ignore[arg-type]
    eventos = list(pipe.responder_stream("xyz"))
    assert len(eventos) == 1
    texto, final = eventos[0]
    assert texto == "No tengo información suficiente"
    assert final is not None
    assert final.archivo_fuente is None
    assert final.fuentes_bm25 == ()
    cliente.chat_stream.assert_not_called()


def test_construir_pipeline_por_defecto_tipo(
    dir_fixtures_markdown: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test:11434")
    pipe = construir_pipeline_por_defecto(dir_fixtures_markdown)
    assert isinstance(pipe, PipelineQa)
