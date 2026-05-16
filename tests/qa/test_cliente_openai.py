"""Pruebas del cliente OpenAI (mock del SDK; sin red)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.laboratorio.qa_legacy.cliente_openai import (
    MODELOS_OPENAI_SOPORTADOS,
    ClienteOpenAi,
    ClaveApiOpenAiAusenteError,
    ConfiguracionOpenai,
    OpenAiClienteError,
)


def test_modeulos_openai_exactamente_cinco_modelos() -> None:
    assert len(MODELOS_OPENAI_SOPORTADOS) == 5
    assert len(set(MODELOS_OPENAI_SOPORTADOS)) == 5


def test_chat_sin_api_key_lanza_esperado() -> None:
    cfg = ConfiguracionOpenai(api_key=None)
    cliente = ClienteOpenAi(cfg)
    with pytest.raises(ClaveApiOpenAiAusenteError) as ei:
        cliente.chat([], modelo="gpt-4o")
    assert ".env" in str(ei.value).lower()


def test_chat_exito_respuesta_llamando_create() -> None:
    cfg = ConfiguracionOpenai(api_key="sk-test-falsa-solo-fixture")
    cliente = ClienteOpenAi(cfg)
    mensajes = [{"role": "user", "content": "hola"}]
    dummy = MagicMock()
    dummy.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Respuesta de prueba"))]
    )

    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy):
        texto = cliente.chat(mensajes, modelo="gpt-4o-mini")

    assert texto == "Respuesta de prueba"
    dummy.chat.completions.create.assert_called_once()
    llamada_kw = dummy.chat.completions.create.call_args.kwargs
    assert llamada_kw["model"] == "gpt-4o-mini"
    assert llamada_kw["messages"] == mensajes
    assert "max_completion_tokens" not in llamada_kw


def test_chat_rate_limit_cadena_en_espanol() -> None:
    from openai import RateLimitError

    cfg = ConfiguracionOpenai(api_key="sk-test")
    cliente = ClienteOpenAi(cfg)
    dummy = MagicMock()
    dummy.chat.completions.create.side_effect = RateLimitError(
        "ignored", response=MagicMock(), body=None
    )

    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy):
        with patch("src.laboratorio.qa_legacy.cliente_openai.time.sleep"):
            with pytest.raises(OpenAiClienteError, match="límite de uso"):
                cliente.chat([{"role": "user", "content": "x"}], modelo="gpt-4o")


def test_chat_rate_limit_tercer_intento_sin_exito() -> None:
    """Tres errores 429 seguidos: se agotan reintentos y el mensaje sugiere gpt-4o-mini."""
    from openai import RateLimitError

    cfg = ConfiguracionOpenai(api_key="sk-test")
    cliente = ClienteOpenAi(cfg)
    dummy = MagicMock()
    dummy.chat.completions.create.side_effect = RateLimitError(
        "rpm",
        response=MagicMock(headers=MagicMock(get=lambda _: None)),
        body=None,
    )

    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy):
        with patch("src.laboratorio.qa_legacy.cliente_openai.time.sleep"):
            with pytest.raises(OpenAiClienteError, match=r"gpt-4o-mini"):
                cliente.chat([{"role": "user", "content": "x"}], modelo="gpt-4o")
    assert dummy.chat.completions.create.call_count == 3


def test_chat_reintenta_una_vez_antes_de_exito() -> None:
    from openai import RateLimitError

    cfg = ConfiguracionOpenai(api_key="sk-test")
    cliente = ClienteOpenAi(cfg)
    dummy = MagicMock()
    ok = MagicMock(
        choices=[MagicMock(message=MagicMock(content="ok tras reintento"))]
    )
    dummy.chat.completions.create.side_effect = [
        RateLimitError("rpm", response=MagicMock(), body=None),
        ok,
    ]

    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy):
        with patch("src.laboratorio.qa_legacy.cliente_openai.time.sleep"):
            texto = cliente.chat([{"role": "user", "content": "."}], modelo="gpt-4o")
    assert texto == "ok tras reintento"
    assert dummy.chat.completions.create.call_count == 2


def test_chat_stream_yield_fragmentos_acumulativos() -> None:
    cfg = ConfiguracionOpenai(api_key="sk-test-falsa-solo-fixture")
    cliente = ClienteOpenAi(cfg)

    def mk_chunk(contenido: str) -> MagicMock:
        f = MagicMock()
        f.choices = [MagicMock(delta=MagicMock(content=contenido))]
        return f

    flujo_mock = iter([mk_chunk("Hel"), mk_chunk("lo"), mk_chunk(" world")])

    dummy = MagicMock()
    dummy.chat.completions.create.return_value = flujo_mock

    salida: list[str] = []
    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy):
        for parte in cliente.chat_stream([{"role": "user", "content": "hi"}], modelo="gpt-4o"):
            salida.append(parte)

    assert "".join(salida) == "Hello world"
    kwargs = dummy.chat.completions.create.call_args.kwargs
    assert kwargs.get("stream") is True


def test_max_completion_tokens_no_se_envia_por_defecto_chat_ni_stream() -> None:
    cfg = ConfiguracionOpenai(api_key="sk-test")
    cliente = ClienteOpenAi(cfg)
    dummy = MagicMock()
    dummy.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="a"))]
    )
    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy):
        cliente.chat([{"role": "user", "content": "x"}], modelo="gpt-4o-mini")
    assert "max_completion_tokens" not in dummy.chat.completions.create.call_args.kwargs

    dummy2 = MagicMock()
    dummy2.chat.completions.create.return_value = iter(())
    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy2):
        list(cliente.chat_stream([{"role": "user", "content": "y"}], modelo="gpt-4o-mini"))
    assert "max_completion_tokens" not in dummy2.chat.completions.create.call_args.kwargs


def test_max_completion_tokens_desde_config_se_envia_chat_y_stream() -> None:
    cfg = ConfiguracionOpenai(api_key="sk-test", max_completion_tokens=777)
    cliente = ClienteOpenAi(cfg)
    dummy = MagicMock()
    dummy.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="ok"))]
    )
    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy):
        cliente.chat([{"role": "user", "content": "."}], modelo="gpt-4o-mini")
    assert dummy.chat.completions.create.call_args.kwargs["max_completion_tokens"] == 777

    dummy2 = MagicMock()
    dummy2.chat.completions.create.return_value = iter(())
    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy2):
        list(cliente.chat_stream([{"role": "user", "content": "."}], modelo="gpt-4o-mini"))
    assert dummy2.chat.completions.create.call_args.kwargs["max_completion_tokens"] == 777


def test_max_completion_tokens_argumento_tiene_prioridad_sobre_config() -> None:
    cfg = ConfiguracionOpenai(api_key="sk-test", max_completion_tokens=100)
    cliente = ClienteOpenAi(cfg)
    dummy = MagicMock()
    dummy.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="z"))]
    )
    with patch("src.laboratorio.qa_legacy.cliente_openai.OpenAI", return_value=dummy):
        cliente.chat(
            [{"role": "user", "content": "a"}],
            modelo="gpt-4o-mini",
            max_completion_tokens=50,
        )
    assert dummy.chat.completions.create.call_args.kwargs["max_completion_tokens"] == 50


def test_max_completion_tokens_env_invalido_es_none(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(
        "src.api.configuracion.obtener_configuracion",
        lambda: SimpleNamespace(
            openai_api_key=None,
            openai_base_url=None,
            openai_timeout_segundos=180.0,
            openai_max_completion_tokens=None,
        ),
    )
    cfg = ConfiguracionOpenai.desde_variables_entorno()
    assert cfg.max_completion_tokens is None


def test_openai_max_completion_tokens_desde_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(
        "src.api.configuracion.obtener_configuracion",
        lambda: SimpleNamespace(
            openai_api_key=None,
            openai_base_url=None,
            openai_timeout_segundos=180.0,
            openai_max_completion_tokens=2048,
        ),
    )
    cfg = ConfiguracionOpenai.desde_variables_entorno()
    assert cfg.max_completion_tokens == 2048
