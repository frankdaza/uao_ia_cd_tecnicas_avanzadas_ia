"""Cliente Ollama: ``num_ctx`` por llamada sin mutar la configuracion global."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.qa.cliente_ollama import ClienteOllama, ConfiguracionLlm


def test_chat_override_num_ctx_en_cuerpo_options() -> None:
    cliente = ClienteOllama(
        ConfiguracionLlm(
            base_url="http://ollama.local",
            modelo="llama3.1:8b",
            num_ctx=8192,
        ),
    )
    cliente._peticion = MagicMock(return_value=MagicMock(  # noqa: SLF001
        status_code=200,
        json=lambda: {"message": {"content": "ok"}},
    ))

    cliente.chat([], num_ctx=4096)

    _args, kwargs = cliente._peticion.call_args  # noqa: SLF001
    json_cuerpo = kwargs["json_cuerpo"]
    assert json_cuerpo["options"]["num_ctx"] == 4096
    assert cliente.configuracion.num_ctx == 8192
