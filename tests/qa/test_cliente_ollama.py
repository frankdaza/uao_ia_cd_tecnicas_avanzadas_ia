"""Pruebas del cliente HTTP de Ollama (mocks y opcionalmente servidor real)."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest
import requests
import responses
from dotenv import load_dotenv

from src.laboratorio.qa_legacy.cliente_ollama import (
    NUM_CTX_MAX,
    NUM_CTX_MIN,
    ClienteOllama,
    ConfiguracionLlm,
    ModeloNoDisponibleError,
    MODELO_LLAMA_3_1_8B,
    OllamaNoAccesibleError,
)


@pytest.fixture
def configuracion() -> ConfiguracionLlm:
    return ConfiguracionLlm(base_url="http://ollama.test", modelo=MODELO_LLAMA_3_1_8B)


@responses.activate
def test_chat_devuelve_contenido_del_modelo(configuracion: ConfiguracionLlm) -> None:
    responses.add(
        responses.POST,
        "http://ollama.test/api/chat",
        json={"message": {"content": "Respuesta simulada"}},
        status=200,
    )
    cliente = ClienteOllama(configuracion)
    texto = cliente.chat([{"role": "user", "content": "Hola"}])
    assert texto == "Respuesta simulada"


@responses.activate
def test_ollama_no_accesible_conexion_rechazada(
    configuracion: ConfiguracionLlm,
) -> None:
    def error_request(*_a: object, **_k: object) -> None:
        raise requests.ConnectionError("Connection refused")

    with patch.object(requests.Session, "request", side_effect=error_request):
        cliente = ClienteOllama(configuracion)
        with pytest.raises(OllamaNoAccesibleError) as ctx:
            cliente.listar_modelos_locales()
    msg = str(ctx.value)
    assert configuracion.base_url in msg
    assert "ollama serve" in msg


@responses.activate
def test_modelo_no_disponible_404(configuracion: ConfiguracionLlm) -> None:
    responses.add(
        responses.POST,
        "http://ollama.test/api/chat",
        json={"error": "model 'x' not found"},
        status=404,
    )
    cliente = ClienteOllama(configuracion)
    with pytest.raises(ModeloNoDisponibleError) as ctx:
        cliente.chat([{"role": "user", "content": "Hola"}])
    msg = str(ctx.value)
    assert configuracion.modelo in msg
    assert "ollama pull" in msg


@responses.activate
def test_modelo_no_disponible_cuerpo_200(configuracion: ConfiguracionLlm) -> None:
    responses.add(
        responses.POST,
        "http://ollama.test/api/chat",
        json={"error": "model 'llama3.1:8b' not found"},
        status=200,
    )
    cliente = ClienteOllama(configuracion)
    with pytest.raises(ModeloNoDisponibleError):
        cliente.chat([{"role": "user", "content": "Hola"}])


@responses.activate
def test_listar_modelos_locales_devuelve_nombres(
    configuracion: ConfiguracionLlm,
) -> None:
    responses.add(
        responses.GET,
        "http://ollama.test/api/tags",
        json={
            "models": [
                {"name": "llama3.1:8b", "size": 1},
                {"name": "gemma4:e2b", "size": 2},
            ]
        },
        status=200,
    )
    cliente = ClienteOllama(configuracion)
    assert cliente.listar_modelos_locales() == ["llama3.1:8b", "gemma4:e2b"]


def test_configuracion_lee_variables_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:11434")
    monkeypatch.setenv("MODELO_LLM_DEFECTO", "gemma4:e2b")
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)
    cfg = ConfiguracionLlm.desde_variables_entorno()
    assert cfg.base_url == "http://custom:11434"
    assert cfg.modelo == "gemma4:e2b"
    assert cfg.num_ctx == 8192


def test_num_ctx_default_sin_ollama_num_ctx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)
    cfg = ConfiguracionLlm.desde_variables_entorno()
    assert cfg.num_ctx == 8192


def test_num_ctx_desde_env_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)
    monkeypatch.setenv("OLLAMA_NUM_CTX", "12288")
    cfg = ConfiguracionLlm.desde_variables_entorno()
    assert cfg.num_ctx == 12288


def test_num_ctx_recortado_a_maximo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_NUM_CTX", "999999")
    cfg = ConfiguracionLlm.desde_variables_entorno()
    assert cfg.num_ctx == NUM_CTX_MAX


def test_num_ctx_recortado_a_minimo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_NUM_CTX", "10")
    cfg = ConfiguracionLlm.desde_variables_entorno()
    assert cfg.num_ctx == NUM_CTX_MIN


def test_num_ctx_invalido_usa_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OLLAMA_NUM_CTX", "foo")
    cfg = ConfiguracionLlm.desde_variables_entorno()
    assert cfg.num_ctx == 8192
    err = capsys.readouterr().err
    assert "OLLAMA_NUM_CTX" in err


@responses.activate
def test_chat_envia_num_ctx_en_options(configuracion: ConfiguracionLlm) -> None:
    configuracion.num_ctx = 12288
    responses.add(
        responses.POST,
        "http://ollama.test/api/chat",
        json={"message": {"content": "ok"}},
        status=200,
    )
    cliente = ClienteOllama(configuracion)
    texto = cliente.chat([{"role": "user", "content": "x"}])
    assert texto == "ok"
    cuerpo = json.loads(responses.calls[0].request.body)
    assert cuerpo["options"]["num_ctx"] == 12288


@responses.activate
def test_reintento_5xx_luego_exito(configuracion: ConfiguracionLlm) -> None:
    responses.add(responses.POST, "http://ollama.test/api/chat", status=503)
    responses.add(
        responses.POST,
        "http://ollama.test/api/chat",
        json={"message": {"content": "ok tras reintento"}},
        status=200,
    )
    cliente = ClienteOllama(configuracion)
    assert cliente.chat([{"role": "user", "content": "x"}]) == "ok tras reintento"
    assert len(responses.calls) == 2


@responses.activate
def test_chat_stream_emite_deltas_ndjson(configuracion: ConfiguracionLlm) -> None:
    cuerpo_ndjson = (
        '{"message":{"content":"Hola "},"done":false}\n'
        '{"message":{"content":"mundo"},"done":false}\n'
        '{"message":{"content":"!"},"done":true}\n'
    )
    responses.add(
        responses.POST,
        "http://ollama.test/api/chat",
        body=cuerpo_ndjson,
        status=200,
        content_type="application/x-ndjson",
    )
    cliente = ClienteOllama(configuracion)
    deltas = list(cliente.chat_stream([{"role": "user", "content": "Hola"}]))
    assert deltas == ["Hola ", "mundo", "!"]
    assert "".join(deltas) == "Hola mundo!"


@responses.activate
def test_chat_stream_modelo_no_disponible_404(
    configuracion: ConfiguracionLlm,
) -> None:
    responses.add(
        responses.POST,
        "http://ollama.test/api/chat",
        json={"error": "model 'x' not found"},
        status=404,
    )
    cliente = ClienteOllama(configuracion)
    with pytest.raises(ModeloNoDisponibleError):
        list(cliente.chat_stream([{"role": "user", "content": "Hola"}]))


def test_chat_stream_ollama_no_accesible(configuracion: ConfiguracionLlm) -> None:
    def error_request(*_a: object, **_k: object) -> None:
        raise requests.ConnectionError("Connection refused")

    with patch.object(requests.Session, "post", side_effect=error_request):
        cliente = ClienteOllama(configuracion)
        with pytest.raises(OllamaNoAccesibleError) as ctx:
            list(cliente.chat_stream([{"role": "user", "content": "Hola"}]))
    assert "ollama serve" in str(ctx.value)


@pytest.mark.integration_ollama
def test_integracion_chat_si_ollama_disponible() -> None:
    load_dotenv()
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    try:
        requests.get(f"{base}/api/tags", timeout=2)
    except (requests.ConnectionError, requests.Timeout):
        pytest.skip("Ollama no accesible en este entorno")
    modelo = os.environ.get("MODELO_LLM_DEFECTO", MODELO_LLAMA_3_1_8B).strip()
    cfg = ConfiguracionLlm(base_url=base, modelo=modelo)
    cliente = ClienteOllama(cfg)
    if cfg.modelo not in cliente.listar_modelos_locales():
        pytest.skip(f"Modelo {cfg.modelo!r} no instalado en Ollama")
    respuesta = cliente.chat([{"role": "user", "content": "Di solo: OK"}])
    assert len(respuesta.strip()) > 0
