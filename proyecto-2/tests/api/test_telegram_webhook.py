"""Pruebas del webhook Telegram (TASK-106)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage

from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram

RUTA_WEBHOOK = "/api/integracion/telegram/webhook"


def _update_mensaje(
    *,
    update_id: int,
    chat_id: int,
    texto: str,
) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id * 10,
            "date": 1_700_000_000,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": chat_id, "is_bot": False, "first_name": "Paciente"},
            "text": texto,
        },
    }


@pytest.fixture
def mensajes_telegram_enviados(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, str]]:
    enviados: list[tuple[int, str]] = []

    async def _capturar(self, chat_id: int, texto: str) -> None:  # noqa: ANN001
        enviados.append((chat_id, texto))

    monkeypatch.setattr(
        "src.integracion.telegram.cliente.ClienteTelegram.enviar_mensaje",
        _capturar,
    )
    return enviados


@pytest.mark.asyncio
async def test_webhook_secret_invalido_403(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.post(
        RUTA_WEBHOOK,
        headers={"X-Telegram-Bot-Api-Secret-Token": "secreto-incorrecto"},
        json=_update_mensaje(update_id=1, chat_id=100, texto="hola"),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_sin_secret_403(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.post(
        RUTA_WEBHOOK,
        json=_update_mensaje(update_id=2, chat_id=101, texto="hola"),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_start_codigo_valido_empareja(
    cliente_api: AsyncClient,
    app_api,
    cabecera_staff: dict[str, str],
    cabecera_telegram: dict[str, str],
    mensajes_telegram_enviados: list[tuple[int, str]],
) -> None:
    from datetime import date

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_t = RepositorioTiposProcedimiento(sesion)
        tipo = await repo_t.crear(
            codigo="tg-start",
            nombre="Procedimiento start",
            indexacion_estado="ok",
        )
        repo_c = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_c.crear(
            paciente_doc_id="CC-TG-START",
            paciente_nombre="Ana Telegram",
            tipo_procedimiento_id=tipo.id,
            cirujano_id="DOC-TG",
            cirujano_nombre="Dr. Telegram",
            fecha_cirugia=date(2026, 5, 1),
        )
        await sesion.commit()
        caso_id = str(caso.id)

    codigo_resp = await cliente_api.post(
        f"/api/staff/casos/{caso_id}/codigo-emparejamiento",
        headers=cabecera_staff,
    )
    assert codigo_resp.status_code == 200
    codigo = codigo_resp.json()["codigo"]
    chat_id = 880001

    resp = await cliente_api.post(
        RUTA_WEBHOOK,
        headers=cabecera_telegram,
        json=_update_mensaje(
            update_id=100,
            chat_id=chat_id,
            texto=f"/start {codigo}",
        ),
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert len(mensajes_telegram_enviados) == 1
    _, texto = mensajes_telegram_enviados[0]
    assert "vinculado correctamente" in texto.lower()
    assert "Ana" in texto


@pytest.mark.asyncio
async def test_mensaje_sin_vinculo_no_invoca_agente(
    cliente_api: AsyncClient,
    cabecera_telegram: dict[str, str],
    mensajes_telegram_enviados: list[tuple[int, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invocado = False

    async def _no_debe_llamarse(**_kwargs):
        nonlocal invocado
        invocado = True
        return {}

    monkeypatch.setattr(
        "src.api.servicios.chat.invocar_agente",
        _no_debe_llamarse,
    )

    resp = await cliente_api.post(
        RUTA_WEBHOOK,
        headers=cabecera_telegram,
        json=_update_mensaje(update_id=200, chat_id=999888, texto="Tengo dolor"),
    )
    assert resp.status_code == 200
    assert invocado is False
    assert len(mensajes_telegram_enviados) == 1
    assert "vinculada" in mensajes_telegram_enviados[0][1].lower()


@pytest.mark.asyncio
async def test_mensaje_vinculado_respuesta_agente(
    cliente_api: AsyncClient,
    app_api,
    cabecera_telegram: dict[str, str],
    mensajes_telegram_enviados: list[tuple[int, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import date

    chat_id = 123456
    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_t = RepositorioTiposProcedimiento(sesion)
        tipo = await repo_t.crear(codigo="tg-webhook", nombre="Proc webhook")
        repo_c = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_c.crear(
            paciente_doc_id="CC-TG-WH",
            paciente_nombre="Paciente Webhook",
            tipo_procedimiento_id=tipo.id,
            cirujano_id="DOC-WH",
            cirujano_nombre="Dr. Webhook",
            fecha_cirugia=date(2026, 5, 10),
        )
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso.id,
            telegram_chat_id=chat_id,
            vinculado_at=datetime.now(UTC),
        )
        await sesion.commit()

    async def _invocar_mock(**_kwargs):
        return {
            "messages": [
                AIMessage(content="Descanse y siga las indicaciones de su protocolo."),
            ]
        }

    monkeypatch.setattr(
        "src.api.servicios.chat.invocar_agente",
        _invocar_mock,
    )

    resp = await cliente_api.post(
        RUTA_WEBHOOK,
        headers=cabecera_telegram,
        json=_update_mensaje(
            update_id=300,
            chat_id=chat_id,
            texto="¿Puedo caminar?",
        ),
    )
    assert resp.status_code == 200
    assert len(mensajes_telegram_enviados) == 1
    assert "protocolo" in mensajes_telegram_enviados[0][1].lower()


@pytest.mark.asyncio
async def test_idempotencia_update_id(
    cliente_api: AsyncClient,
    app_api,
    cabecera_telegram: dict[str, str],
    mensajes_telegram_enviados: list[tuple[int, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import date

    chat_id = 444555
    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_t = RepositorioTiposProcedimiento(sesion)
        tipo = await repo_t.crear(codigo="tg-idem", nombre="Proc idem")
        repo_c = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_c.crear(
            paciente_doc_id="CC-TG-IDEM",
            paciente_nombre="Paciente Idem",
            tipo_procedimiento_id=tipo.id,
            cirujano_id="DOC-ID",
            cirujano_nombre="Dr. Idem",
            fecha_cirugia=date(2026, 5, 11),
        )
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso.id,
            telegram_chat_id=chat_id,
            vinculado_at=datetime.now(UTC),
        )
        await sesion.commit()

    async def _invocar_mock(**_kwargs):
        return {"messages": [AIMessage(content="Respuesta unica.")]}

    monkeypatch.setattr(
        "src.api.servicios.chat.invocar_agente",
        _invocar_mock,
    )

    cuerpo = _update_mensaje(update_id=400, chat_id=chat_id, texto="Hola")
    for _ in range(2):
        resp = await cliente_api.post(
            RUTA_WEBHOOK,
            headers=cabecera_telegram,
            json=cuerpo,
        )
        assert resp.status_code == 200

    assert len(mensajes_telegram_enviados) == 1
