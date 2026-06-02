"""Pruebas de recordatorios Telegram (UC-MVP-04 / TASK-107)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from src.integracion.recordatorios.servicio import (
    disparar_recordatorio_prueba,
    procesar_recordatorios_pendientes,
)
from src.integracion.telegram.cliente import ClienteTelegram
from src.persistencia.demo_ids import CHAT_TELEGRAM_CASO_A
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.plantillas_recordatorio import (
    RepositorioPlantillasRecordatorio,
)
from src.persistencia.repositorios.recordatorios_enviados import (
    RepositorioRecordatoriosEnviados,
)
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram
from tests.api.conftest import PDF_FIXTURE_MINIMO
from tests.api.test_staff_casos import _cuerpo_caso


@pytest.fixture
async def tipo_procedimiento_ok(
    app_api,
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> str:
    import json

    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files={
            "metadata": (
                None,
                json.dumps(
                    {"codigo": f"rec-{uuid.uuid4().hex[:6]}", "nombre": "Procedimiento Recordatorio"}
                ),
                "application/json",
            ),
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    assert crear.status_code == 201
    tipo_id = uuid.UUID(crear.json()["id"])

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo = RepositorioTiposProcedimiento(sesion)
        fila = await repo.obtener_por_id(tipo_id)
        assert fila is not None
        await repo.actualizar(fila, indexacion_estado="ok")
        await sesion.commit()

    return str(tipo_id)


@pytest.mark.asyncio
async def test_crear_caso_genera_plantillas_y_recordatorios(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    resp = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(tipo_id=tipo_procedimiento_ok),
    )
    assert resp.status_code == 201
    caso_id = uuid.UUID(resp.json()["id"])

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_pl = RepositorioPlantillasRecordatorio(sesion)
        plantillas = await repo_pl.listar_por_tipo(uuid.UUID(tipo_procedimiento_ok))
        assert len(plantillas) >= 3

        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        pendientes = await repo_rec.listar_pendientes_vencidos(
            ahora=datetime(2099, 1, 1, tzinfo=UTC),
        )
        del pendientes  # puede estar vacio si aun no vencen
        stmt_caso = await RepositorioCasosPostoperatorio(sesion).obtener_por_id(caso_id)
        assert stmt_caso is not None
        siguiente = await repo_rec.obtener_siguiente_pendiente_caso(caso_id)
        assert siguiente is not None


@pytest.mark.asyncio
async def test_job_envia_recordatorio_vencido(
    app_api,
    tipo_procedimiento_ok: str,
) -> None:
    factory = app_api.state.session_factory
    tipo_id = uuid.UUID(tipo_procedimiento_ok)
    chat_id = 990_001_107

    async with factory() as sesion:
        repo_casos = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_casos.crear(
            paciente_doc_id="CC-REC-1",
            paciente_nombre="Paciente Recordatorio",
            tipo_procedimiento_id=tipo_id,
            cirujano_id="MED-REC",
            cirujano_nombre="Dr. Demo",
            fecha_cirugia=date.today() - timedelta(days=2),
            estado="activo",
        )
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso.id,
            telegram_chat_id=chat_id,
            vinculado_at=datetime.now(UTC),
        )
        repo_pl = RepositorioPlantillasRecordatorio(sesion)
        await repo_pl.crear(
            tipo_procedimiento_id=tipo_id,
            tipo="medicacion",
            offset_horas_desde_cirugia=0,
            texto_plantilla="Hola {nombre_paciente}, {tipo_procedimiento}: {texto_cuidado}",
        )
        plantilla = (await repo_pl.listar_por_tipo(tipo_id))[0]
        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        await repo_rec.crear(
            caso_id=caso.id,
            plantilla_id=plantilla.id,
            programado_at=datetime.now(UTC) - timedelta(hours=1),
        )
        await sesion.commit()

    enviados_capturados: list[tuple[int, str]] = []

    async def _capturar(chat_id: int, texto: str) -> None:
        enviados_capturados.append((chat_id, texto))

    cliente_mock = AsyncMock(spec=ClienteTelegram)
    cliente_mock.enviar_mensaje = _capturar

    cantidad = await procesar_recordatorios_pendientes(
        factory,
        cliente_telegram=cliente_mock,
    )
    assert cantidad == 1
    assert len(enviados_capturados) == 1
    assert enviados_capturados[0][0] == chat_id
    assert "Paciente Recordatorio" in enviados_capturados[0][1]


@pytest.mark.asyncio
async def test_disparar_recordatorio_prueba_sin_vinculo(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    crear = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(tipo_id=tipo_procedimiento_ok, doc_id="CC-REC-SIN-TG"),
    )
    assert crear.status_code == 201
    caso_id = crear.json()["id"]

    resp = await cliente_api.post(
        f"/api/staff/casos/{caso_id}/disparar-recordatorio-prueba",
        headers=cabecera_staff,
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["enviado"] is False
    assert cuerpo["motivo_omitido"] == "sin_vinculo_telegram"


@pytest.mark.asyncio
async def test_disparar_recordatorio_prueba_envia_con_vinculo(
    app_api,
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crear = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(tipo_id=tipo_procedimiento_ok, doc_id="CC-REC-CON-TG"),
    )
    assert crear.status_code == 201
    caso_id = uuid.UUID(crear.json()["id"])
    chat_id = 990_002_107

    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso_id,
            telegram_chat_id=chat_id,
            vinculado_at=datetime.now(UTC),
        )
        await sesion.commit()

    enviados: list[str] = []

    async def _mock_enviar(self, chat_id: int, texto: str) -> None:
        enviados.append(texto)

    monkeypatch.setattr(ClienteTelegram, "enviar_mensaje", _mock_enviar)

    resp = await cliente_api.post(
        f"/api/staff/casos/{caso_id}/disparar-recordatorio-prueba",
        headers=cabecera_staff,
    )

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["enviado"] is True
    assert len(enviados) == 1
    assert "Paciente Demo A" in enviados[0]


@pytest.mark.asyncio
async def test_job_omite_chat_id_demo_ficticio(
    app_api,
    tipo_procedimiento_ok: str,
) -> None:
    factory = app_api.state.session_factory
    tipo_id = uuid.UUID(tipo_procedimiento_ok)

    async with factory() as sesion:
        repo_casos = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_casos.crear(
            paciente_doc_id="CC-REC-DEMO-CHAT",
            paciente_nombre="Paciente Demo Chat",
            tipo_procedimiento_id=tipo_id,
            cirujano_id="MED-REC",
            cirujano_nombre="Dr. Demo",
            fecha_cirugia=date.today() - timedelta(days=2),
            estado="activo",
        )
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso.id,
            telegram_chat_id=CHAT_TELEGRAM_CASO_A,
            vinculado_at=datetime.now(UTC),
        )
        repo_pl = RepositorioPlantillasRecordatorio(sesion)
        await repo_pl.crear(
            tipo_procedimiento_id=tipo_id,
            tipo="medicacion",
            offset_horas_desde_cirugia=0,
            texto_plantilla="Hola {nombre_paciente}, {tipo_procedimiento}: {texto_cuidado}",
        )
        plantilla = (await repo_pl.listar_por_tipo(tipo_id))[0]
        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        await repo_rec.crear(
            caso_id=caso.id,
            plantilla_id=plantilla.id,
            programado_at=datetime.now(UTC) - timedelta(hours=1),
        )
        await sesion.commit()

    cliente_mock = AsyncMock(spec=ClienteTelegram)

    cantidad = await procesar_recordatorios_pendientes(
        factory,
        cliente_telegram=cliente_mock,
    )
    assert cantidad == 0
    cliente_mock.enviar_mensaje.assert_not_called()


@pytest.mark.asyncio
async def test_disparar_recordatorio_omite_chat_demo_ficticio(
    app_api,
    tipo_procedimiento_ok: str,
) -> None:
    factory = app_api.state.session_factory
    tipo_id = uuid.UUID(tipo_procedimiento_ok)

    async with factory() as sesion:
        repo_casos = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_casos.crear(
            paciente_doc_id="CC-REC-DEMO-DISPARO",
            paciente_nombre="Paciente Demo Disparo",
            tipo_procedimiento_id=tipo_id,
            cirujano_id="MED-REC",
            cirujano_nombre="Dr. Demo",
            fecha_cirugia=date.today(),
            estado="activo",
        )
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso.id,
            telegram_chat_id=CHAT_TELEGRAM_CASO_A,
            vinculado_at=datetime.now(UTC),
        )
        repo_pl = RepositorioPlantillasRecordatorio(sesion)
        await repo_pl.crear(
            tipo_procedimiento_id=tipo_id,
            tipo="medicacion",
            offset_horas_desde_cirugia=24,
            texto_plantilla="Hola {nombre_paciente}, {tipo_procedimiento}: {texto_cuidado}",
        )
        plantilla = (await repo_pl.listar_por_tipo(tipo_id))[0]
        repo_rec = RepositorioRecordatoriosEnviados(sesion)
        await repo_rec.crear(
            caso_id=caso.id,
            plantilla_id=plantilla.id,
            programado_at=datetime.now(UTC) + timedelta(hours=1),
        )
        await sesion.commit()
        caso_id = caso.id

    async with factory() as sesion:
        resultado = await disparar_recordatorio_prueba(sesion, caso_id)
        await sesion.commit()

    assert resultado.enviado is False
    assert resultado.motivo_omitido == "chat_demo_ficticio"


@pytest.mark.asyncio
async def test_sin_uso_de_email_en_modulo_recordatorios() -> None:
    """UC-MVP-04: canal exclusivo Telegram; sin SMTP/email en el paquete."""
    import src.integracion.recordatorios.servicio as mod

    fuente = open(mod.__file__, encoding="utf-8").read().lower()
    assert "smtplib" not in fuente
    assert "send_mail" not in fuente
    assert "@aiosmtplib" not in fuente
