"""
E2E de los cuatro escenarios del Modulo 2 (PDF de la actividad).

Requieren API levantada (p. ej. ``docker compose up``) y::

    EJECUTAR_E2E_MODULO2=1 uv run pytest tests/e2e/test_escenarios_modulo2.py

Variables utiles: ``BASE_URL`` o ``E2E_BASE_URL``, ``MOCK_LLM=1`` en el servidor
para aserciones deterministas sobre la herramienta (tokens ``e2e7001`` / ``e2e7002`` / ``e2e7003``).

Con LLM real (sin ``MOCK_LLM``), definir ``E2E_LLM_REAL=1`` para omitir aserciones estrictas
de herramienta (solo se valida flujo SSE y evento ``final``). El escenario (b) puede seguir
siendo **fragil** con LLM real por la memoria conversacional.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from tests.e2e.util_sse import parsear_eventos_sse


async def _consumir_agente_sse(
    client: httpx.AsyncClient,
    *,
    session_id: str,
    pregunta: str,
    primer_turno: bool,
) -> list[tuple[str, dict[str, Any]]]:
    cabeceras = {"X-Session-Id": session_id}
    async with client.stream(
        "POST",
        "/api/agente/stream",
        headers=cabeceras,
        json={
            "session_id": session_id,
            "pregunta": pregunta,
            "primer_turno": primer_turno,
        },
    ) as respuesta:
        if respuesta.status_code == 503:
            pytest.skip(
                "Grafo del agente no disponible (HTTP 503). Revise OPENAI_API_KEY o MOCK_LLM=1."
            )
        if respuesta.status_code == 401:
            pytest.skip("Sesion no autorizada (HTTP 401).")
        assert respuesta.status_code == 200, await respuesta.aread()
        cuerpo = await respuesta.aread()
    return parsear_eventos_sse(cuerpo)


def _herramientas_por_turno(eventos: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Incluye candidatas del router y nombre emitido al ejecutar la tool (puede repetirse)."""
    orden: list[str] = []
    for nombre, payload in eventos:
        if nombre == "pensamiento" and payload.get("herramienta_candidata"):
            orden.append(str(payload["herramienta_candidata"]))
        elif nombre == "herramienta" and payload.get("nombre"):
            orden.append(str(payload["nombre"]))
    return orden


def _herramientas_ejecutadas(eventos: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Solo eventos ``herramienta`` (una entrada por invocacion de tool)."""
    return [
        str(p["nombre"]) for e, p in eventos if e == "herramienta" and p.get("nombre")
    ]


async def _salud_mock_llm(client: httpx.AsyncClient) -> bool | None:
    r = await client.get("/api/salud")
    if r.status_code != 200:
        return None
    data = r.json()
    return data.get("agente_mock_llm")


@pytest.mark.e2e_modulo2
@pytest.mark.asyncio
async def test_e2e_escenario_a_rag_denso(
    cliente_http_e2e: httpx.AsyncClient,
    sesion_m2_e2e: dict[str, str],
    e2e_modo_llm_real: bool,
) -> None:
    """(a) Consulta abierta que en MOCK_LLM fuerza ``rag_denso`` y emite fuentes o metricas coherentes."""
    mock = await _salud_mock_llm(cliente_http_e2e)
    if mock is not True and not e2e_modo_llm_real:
        pytest.skip(
            "Este escenario estricto requiere MOCK_LLM=1 en el servidor (o defina E2E_LLM_REAL=1)."
        )
    sid = sesion_m2_e2e["session_id"]
    pregunta = (
        "Explique de forma amplia como la fundacion articula calidad y seguridad del paciente "
        "segun documentacion institucional. e2e7001"
    )
    eventos = await _consumir_agente_sse(
        cliente_http_e2e,
        session_id=sid,
        pregunta=pregunta,
        primer_turno=True,
    )
    tipos = [e for e, _ in eventos]
    assert "final" in tipos
    if mock is True:
        assert "rag_denso" in _herramientas_por_turno(eventos)
        assert "herramienta" in tipos


@pytest.mark.e2e_modulo2
@pytest.mark.asyncio
async def test_e2e_escenario_b_memoria_dos_turnos(
    cliente_http_e2e: httpx.AsyncClient,
    sesion_m2_e2e: dict[str, str],
    e2e_modo_llm_real: bool,
) -> None:
    """(b) Dos turnos: el segundo depende del primero (referencia al color)."""
    mock = await _salud_mock_llm(cliente_http_e2e)
    if mock is not True and not e2e_modo_llm_real:
        pytest.skip(
            "Este escenario estricto requiere MOCK_LLM=1 en el servidor (o defina E2E_LLM_REAL=1)."
        )
    sid = sesion_m2_e2e["session_id"]
    t1 = "Mi color favorito es azul. Confirma que registraste mi preferencia. e2e7001"
    ev1 = await _consumir_agente_sse(
        cliente_http_e2e,
        session_id=sid,
        pregunta=t1,
        primer_turno=True,
    )
    assert any(e == "final" for e, _ in ev1)
    t2 = "Cual era mi color favorito que te mencione antes? e2e7003"
    ev2 = await _consumir_agente_sse(
        cliente_http_e2e,
        session_id=sid,
        pregunta=t2,
        primer_turno=False,
    )
    texto_final = ""
    for nombre, payload in ev2:
        if nombre == "final":
            texto_final = str(payload.get("texto") or "")
    assert "azul" in texto_final.lower()
    if mock is True:
        assert "rag_denso" in _herramientas_por_turno(ev2)


@pytest.mark.e2e_modulo2
@pytest.mark.asyncio
async def test_e2e_escenario_c_faq_estructurada(
    cliente_http_e2e: httpx.AsyncClient,
    sesion_m2_e2e: dict[str, str],
    e2e_modo_llm_real: bool,
) -> None:
    """(c) Pregunta tipo horario / contacto que en MOCK_LLM fuerza ``faq_estructurada``."""
    mock = await _salud_mock_llm(cliente_http_e2e)
    if mock is not True and not e2e_modo_llm_real:
        pytest.skip(
            "Este escenario estricto requiere MOCK_LLM=1 en el servidor (o defina E2E_LLM_REAL=1)."
        )
    sid = sesion_m2_e2e["session_id"]
    pregunta = "Cual es el horario de atencion del SIAU PQRS? e2e7002"
    eventos = await _consumir_agente_sse(
        cliente_http_e2e,
        session_id=sid,
        pregunta=pregunta,
        primer_turno=True,
    )
    assert "final" in [e for e, _ in eventos]
    if mock is True:
        assert "faq_estructurada" in _herramientas_por_turno(eventos)


@pytest.mark.e2e_modulo2
@pytest.mark.asyncio
async def test_e2e_escenario_d_mixto_misma_sesion(
    cliente_http_e2e: httpx.AsyncClient,
    sesion_m2_e2e: dict[str, str],
    e2e_modo_llm_real: bool,
) -> None:
    """(d) Varios turnos en la misma sesion: alternancia FAQ / RAG verificable con MOCK_LLM."""
    mock = await _salud_mock_llm(cliente_http_e2e)
    if mock is not True and not e2e_modo_llm_real:
        pytest.skip(
            "Este escenario estricto requiere MOCK_LLM=1 en el servidor (o defina E2E_LLM_REAL=1)."
        )
    sid = sesion_m2_e2e["session_id"]
    turnos = [
        ("Cual es el telefono PBX general? e2e7002", True),
        ("Resume lineas estrategicas institucionales amplias. e2e7001", False),
        ("NIT y razon social de la fundacion? e2e7002", False),
    ]
    ejecutadas: list[str] = []
    for texto, primero in turnos:
        ev = await _consumir_agente_sse(
            cliente_http_e2e,
            session_id=sid,
            pregunta=texto,
            primer_turno=primero,
        )
        assert "final" in [e for e, _ in ev]
        ejecutadas.extend(_herramientas_ejecutadas(ev))
    if mock is True:
        assert ejecutadas == ["faq_estructurada", "rag_denso", "faq_estructurada"]
