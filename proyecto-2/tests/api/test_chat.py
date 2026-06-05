"""Pruebas de ``POST /chat`` (TASK-104)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage

from src.agentes.guardrails_alcance import MENSAJE_FUERA_DE_ALCANCE, ResultadoAlcance
from src.agentes.servicio import extraer_fuentes_respuesta, extraer_severidad_triage
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram


async def _sembrar_vinculo_telegram_123(app_api) -> None:
    from datetime import date

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_t = RepositorioTiposProcedimiento(sesion)
        tipo = await repo_t.crear(codigo="chat-demo", nombre="Procedimiento chat")
        repo_c = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_c.crear(
            paciente_doc_id="CC-CHAT-1",
            paciente_nombre="Paciente Chat",
            tipo_procedimiento_id=tipo.id,
            cirujano_id="DOC-CHAT",
            cirujano_nombre="Dr. Chat",
            fecha_cirugia=date(2026, 5, 1),
        )
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso.id,
            telegram_chat_id=123,
            vinculado_at=datetime.now(UTC),
        )
        await sesion.commit()


@pytest.mark.asyncio
async def test_chat_200_respuesta_mock(
    cliente_api: AsyncClient,
    app_api,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _sembrar_vinculo_telegram_123(app_api)

    async def _invocar_mock(**_kwargs):
        return {
            "messages": [
                AIMessage(content="Puede caminar con moderacion segun su protocolo."),
            ]
        }

    monkeypatch.setattr(
        "src.api.servicios.chat.invocar_agente",
        _invocar_mock,
    )

    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:123",
            "mensaje": "¿Cuando puedo caminar?",
            "metadata": {"canal": "telegram", "update_id": 99},
        },
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["respuesta"].strip()
    assert cuerpo["requiere_revision_humana"] is False
    assert cuerpo["error"] is None


@pytest.mark.asyncio
async def test_chat_crea_alerta_urgente_sin_escalar(
    cliente_api: AsyncClient,
    app_api,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tras el turno, asegurar_alerta_desde_turno persiste alerta si solo hubo clasificacion."""
    await _sembrar_vinculo_telegram_123(app_api)
    mensaje = "Tengo mucho sangrado, creo que se me abrio la herida"

    async def _invocar_mock(**_kwargs):
        from langchain_core.messages import ToolMessage

        return {
            "messages": [
                ToolMessage(
                    content='{"severidad": "urgente", "rationale": "Sangrado detectado."}',
                    name="clasificar_triage",
                    tool_call_id="1",
                ),
            ]
        }

    monkeypatch.setattr(
        "src.api.servicios.chat.invocar_agente",
        _invocar_mock,
    )

    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:123",
            "mensaje": mensaje,
            "metadata": {"canal": "telegram", "update_id": 100},
        },
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["severidad_triage"] == "urgente"
    assert cuerpo["requiere_revision_humana"] is False

    from sqlalchemy import select

    from src.persistencia.modelos import AlertaTriage

    factory = app_api.state.session_factory
    async with factory() as sesion:
        res = await sesion.execute(select(AlertaTriage))
        filas = list(res.scalars().all())
    assert len(filas) == 1
    assert filas[0].severidad == "urgente"
    assert filas[0].mensaje_paciente_ref == mensaje


@pytest.mark.asyncio
async def test_chat_rechaza_python_heuristica_sin_ainvoke(
    cliente_api: AsyncClient,
    app_api,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Integracion real del guardrail (sin mockear evaluar_alcance_consulta)."""
    await _sembrar_vinculo_telegram_123(app_api)

    agente_ainvoke_llamado = False

    def _construir_agente_espiado(checkpointer, cfg=None, hitl_escalar_habilitado=None):
        from src.agentes.agente_taam import construir_agente_taam

        agente = construir_agente_taam(
            checkpointer,
            cfg=cfg,
            hitl_escalar_habilitado=hitl_escalar_habilitado,
        )
        original_ainvoke = agente.ainvoke

        async def _ainvoke_espiado(*args, **kwargs):
            nonlocal agente_ainvoke_llamado
            agente_ainvoke_llamado = True
            return await original_ainvoke(*args, **kwargs)

        agente.ainvoke = _ainvoke_espiado  # type: ignore[method-assign]
        return agente

    monkeypatch.setattr(
        "src.agentes.servicio.construir_agente_taam",
        _construir_agente_espiado,
    )

    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:123",
            "mensaje": "¿Cómo hago un hola mundo en Python?",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["respuesta"] == MENSAJE_FUERA_DE_ALCANCE
    assert agente_ainvoke_llamado is False


@pytest.mark.asyncio
async def test_chat_rechaza_fuera_alcance_sin_ainvoke_agente(
    cliente_api: AsyncClient,
    app_api,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _sembrar_vinculo_telegram_123(app_api)

    agente_ainvoke_llamado = False

    async def _alcance_fuera(_mensaje: str, _cfg=None) -> ResultadoAlcance:
        return ResultadoAlcance(en_alcance=False, motivo="test_fuera")

    def _construir_agente_espiado(checkpointer, cfg=None, hitl_escalar_habilitado=None):
        from src.agentes.agente_taam import construir_agente_taam

        agente = construir_agente_taam(
            checkpointer,
            cfg=cfg,
            hitl_escalar_habilitado=hitl_escalar_habilitado,
        )
        original_ainvoke = agente.ainvoke

        async def _ainvoke_espiado(*args, **kwargs):
            nonlocal agente_ainvoke_llamado
            agente_ainvoke_llamado = True
            return await original_ainvoke(*args, **kwargs)

        agente.ainvoke = _ainvoke_espiado  # type: ignore[method-assign]
        return agente

    monkeypatch.setattr(
        "src.agentes.servicio.evaluar_alcance_consulta",
        _alcance_fuera,
    )
    monkeypatch.setattr(
        "src.agentes.servicio.construir_agente_taam",
        _construir_agente_espiado,
    )

    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:123",
            "mensaje": "¿Cómo hago un hola mundo en Python?",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["respuesta"] == MENSAJE_FUERA_DE_ALCANCE
    assert agente_ainvoke_llamado is False


@pytest.mark.asyncio
async def test_chat_403_sin_vinculo(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:999",
            "mensaje": "Hola",
        },
    )
    assert resp.status_code == 403
    detalle = resp.json()["detail"]
    assert "vinculada" in detalle.lower() or "vincul" in detalle.lower()
    assert "codigo" in detalle.lower() or "emparejamiento" in detalle.lower()


@pytest.mark.asyncio
async def test_chat_503_timeout(
    cliente_api: AsyncClient,
    app_api,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _sembrar_vinculo_telegram_123(app_api)

    async def _invocar_timeout(**_kwargs):
        raise TimeoutError()

    monkeypatch.setattr(
        "src.api.servicios.chat.invocar_agente",
        _invocar_timeout,
    )

    resp = await cliente_api.post(
        "/chat",
        json={
            "session_id": "telegram:123",
            "mensaje": "Consulta lenta",
        },
    )
    assert resp.status_code == 503
    detalle = resp.json()["detail"]
    assert "tiempo" in detalle.lower() or "respondio" in detalle.lower()
    assert "sk-" not in detalle
    assert "OPENAI" not in detalle.upper()


@pytest.mark.asyncio
async def test_openapi_documenta_chat(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.get("/openapi.json")
    assert resp.status_code == 200
    esquema = resp.json()
    assert "ChatPeticion" in esquema["components"]["schemas"]
    assert "ChatRespuesta" in esquema["components"]["schemas"]
    rutas = esquema["paths"]
    assert "/chat" in rutas
    assert "post" in rutas["/chat"]
    tags = rutas["/chat"]["post"].get("tags", [])
    assert "chat" in tags


def test_extraer_severidad_y_fuentes_desde_estado() -> None:
    from langchain_core.messages import ToolMessage

    estado = {
        "messages": [
            ToolMessage(
                content='{"severidad": "urgente", "rationale": "Alarma"}',
                name="clasificar_triage",
                tool_call_id="1",
            ),
            ToolMessage(
                content="[1] Evitar esfuerzo intenso.\n\n[2] Control de herida diario.",
                name="consultar_protocolo_rag",
                tool_call_id="2",
            ),
        ]
    }
    assert extraer_severidad_triage(estado) == "urgente"
    fuentes = extraer_fuentes_respuesta(estado)
    assert len(fuentes) == 2
    assert fuentes[0]["titulo"] == "Protocolo [1]"
