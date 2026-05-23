"""Pruebas de repositorios TAAM con SQLite (FK y unicidad)."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from src.persistencia.repositorios import (
    RepositorioAlertasTriage,
    RepositorioCasosPostoperatorio,
    RepositorioTiposProcedimiento,
    RepositorioVinculosTelegram,
)


@pytest.mark.asyncio
async def test_caso_requiere_tipo_procedimiento_existente(sesion_sqlite) -> None:
    repo_casos = RepositorioCasosPostoperatorio(sesion_sqlite)
    import uuid

    with pytest.raises(IntegrityError):
        await repo_casos.crear(
            paciente_doc_id="CC-100",
            paciente_nombre="Paciente Demo",
            tipo_procedimiento_id=uuid.uuid4(),
            cirujano_id="MED-1",
            cirujano_nombre="Dr. Demo",
            fecha_cirugia=date(2026, 5, 1),
        )
        await sesion_sqlite.commit()


@pytest.mark.asyncio
async def test_flujo_minimo_y_unicidad_telegram_chat_id(sesion_sqlite) -> None:
    repo_tipos = RepositorioTiposProcedimiento(sesion_sqlite)
    repo_casos = RepositorioCasosPostoperatorio(sesion_sqlite)
    repo_vinculos = RepositorioVinculosTelegram(sesion_sqlite)
    repo_alertas = RepositorioAlertasTriage(sesion_sqlite)

    tipo = await repo_tipos.crear(codigo="COLE-LAP-001", nombre="Colecistectomia laparoscopica")
    caso = await repo_casos.crear(
        paciente_doc_id="CC-200",
        paciente_nombre="Maria Demo",
        tipo_procedimiento_id=tipo.id,
        cirujano_id="MED-2",
        cirujano_nombre="Dr. Cirujano",
        fecha_cirugia=date(2026, 5, 10),
    )
    await repo_vinculos.crear(caso_id=caso.id, telegram_chat_id=90001)
    await repo_alertas.crear(
        caso_id=caso.id,
        severidad="urgente",
        resumen="Sangrado abundante",
        mensaje_paciente_ref="ref-msg-1",
    )
    await sesion_sqlite.commit()

    assert len(await repo_tipos.listar()) == 1
    assert len(await repo_casos.listar(estado="activo")) == 1
    assert (await repo_vinculos.obtener_por_chat_id(90001)) is not None
    assert len(await repo_alertas.listar(revisado=False)) == 1

    with pytest.raises(IntegrityError):
        await repo_vinculos.crear(caso_id=caso.id, telegram_chat_id=90001)
        await sesion_sqlite.commit()
