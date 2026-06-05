"""Pruebas del guardrail de alcance postoperatorio (Lili Bot)."""

from __future__ import annotations

import pytest

from src.agentes.guardrails_alcance import (
    MENSAJE_FUERA_DE_ALCANCE,
    ResultadoAlcance,
    evaluar_alcance_consulta,
)
from src.configuracion import Configuracion


@pytest.mark.asyncio
async def test_heuristica_rechaza_programacion_python() -> None:
    cfg = Configuracion.model_construct(agente_guardrails_habilitado=True)
    resultado = await evaluar_alcance_consulta(
        "¿Cómo hago un hola mundo en Python?",
        cfg,
    )
    assert resultado.en_alcance is False
    assert resultado.motivo == "heuristica_fuera"


@pytest.mark.asyncio
async def test_heuristica_acepta_fiebre_postoperatoria() -> None:
    cfg = Configuracion.model_construct(agente_guardrails_habilitado=True)
    resultado = await evaluar_alcance_consulta(
        "Tengo fiebre alta después de la cirugía",
        cfg,
    )
    assert resultado.en_alcance is True
    assert resultado.motivo == "heuristica_dentro"


@pytest.mark.asyncio
async def test_heuristica_acepta_caminar() -> None:
    cfg = Configuracion.model_construct(agente_guardrails_habilitado=True)
    resultado = await evaluar_alcance_consulta(
        "¿Cuándo puedo caminar?",
        cfg,
    )
    assert resultado.en_alcance is True
    assert resultado.motivo == "heuristica_dentro"


@pytest.mark.asyncio
async def test_heuristica_acepta_saludo_hola() -> None:
    cfg = Configuracion.model_construct(agente_guardrails_habilitado=True)
    resultado = await evaluar_alcance_consulta("Hola", cfg)
    assert resultado.en_alcance is True
    assert resultado.motivo == "saludo_corto"


@pytest.mark.asyncio
async def test_guardrails_desactivados_permiten_todo() -> None:
    cfg = Configuracion.model_construct(agente_guardrails_habilitado=False)
    resultado = await evaluar_alcance_consulta(
        "¿Cómo hago un hola mundo en Python?",
        cfg,
    )
    assert resultado.en_alcance is True
    assert resultado.motivo == "guardrails_desactivados"


_MENSAJE_DUDOSO = "¿Me podria orientar un poco mas sobre esto?"


@pytest.mark.asyncio
async def test_dudoso_usa_llm_cuando_hay_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _mock_llm(_mensaje: str, _cfg: Configuracion) -> ResultadoAlcance:
        return ResultadoAlcance(en_alcance=False, motivo="llm:finanzas")

    monkeypatch.setattr(
        "src.agentes.guardrails_alcance._clasificar_con_llm",
        _mock_llm,
    )
    cfg = Configuracion.model_construct(
        agente_guardrails_habilitado=True,
        openai_api_key="sk-test",
        agente_modelo="openai:gpt-4o-mini",
    )
    resultado = await evaluar_alcance_consulta(_MENSAJE_DUDOSO, cfg)
    assert resultado.en_alcance is False
    assert resultado.motivo.startswith("llm:")


@pytest.mark.asyncio
async def test_dudoso_sin_api_permite_agente() -> None:
    cfg = Configuracion.model_construct(
        agente_guardrails_habilitado=True,
        openai_api_key="",
    )
    resultado = await evaluar_alcance_consulta(_MENSAJE_DUDOSO, cfg)
    assert resultado.en_alcance is True
    assert resultado.motivo == "dudoso_sin_api_clasificador"


def test_mensaje_fuera_de_alcance_no_vacio() -> None:
    assert "postoperatorio" in MENSAJE_FUERA_DE_ALCANCE.lower()
